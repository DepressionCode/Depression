from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from datetime import datetime
from pymysql.err import IntegrityError
import pymysql
import re
import os
import hashlib
import random
import uuid
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif', 'gif'}
app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'
app.config["UPLOAD_FOLDER"] = "./static/Images/"
app.config['UPLOAD_FOLDER2'] = 'FlaskWebProject/static/post_images/'

UPLOAD_FOLDER2 = app.config['UPLOAD_FOLDER2']

if not os.path.exists(UPLOAD_FOLDER2):
    os.makedirs(UPLOAD_FOLDER2)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

def create_connection():
    # Connect to the database
    return pymysql.connect(host='10.0.0.17',
                                 user='johvu',
                                 password='AISLE',
                                 database='johvu',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)


@app.route('/', methods=['GET', 'POST'])
def login():
    # Connect to the database
    with create_connection() as connection:
        # Output message if something goes wrong...
        msg = ''
        # Check if "username" and "password" POST requests exist (user submitted form)
        if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
            # Create variables for easy access
            email = request.form['email']
            password = request.form['password']
            encrypted_password = hashlib.sha256(password.encode()).hexdigest()
            # Check if account exists using MySQL
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM tblusers WHERE email = %s AND password = %s', (email, encrypted_password,))
                # Fetch one record and return result
                account = cursor.fetchone()
            # If account exists in accounts table in out database
            if account:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['user_id'] = account['user_id']
                session['role_id'] = account['role_id']
                session['email'] = account['email']
                session['first_name'] = account['first_name']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect email/password!'
        # Show the login form with message (if any)
        return render_template('index.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('user_id', None)
   session.pop('first_name', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Connect to the database
    with create_connection() as connection:
        # Output message if something goes wrong...
        msg = ''
        # Check if "username", "password" and "email" POST requests exist (user submitted form)
        if request.method == 'POST' and 'first_name' in request.form and 'password' in request.form and 'email' in request.form:
            # Create variables for easy access
            username = request.form['first_name']
            password = request.form['password']
            email = request.form['email']
            encrypted_password = hashlib.sha256(password.encode()).hexdigest()
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM tblusers WHERE email = %s', (email))
                # Fetch one record and return result
                account = cursor.fetchone()
                # If account exists show error and validation checks
                if account:
                    msg = 'Cannot use the same email!'
                elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                    msg = 'Invalid email address!'
                elif not re.match(r'[A-Za-z0-9]+', username):
                    msg = 'Username must contain only characters and numbers!'
                elif not re.match(r'[A-Za-z0-9]+', password):
                    msg = 'password must contain only characters and numbers!'
                elif not username or not password or not email:
                    msg = 'Please fill out the form!'
                else:
                    # Account doesnt exists and the form data is valid, now insert new account into accounts table
                    cursor.execute('INSERT INTO tblusers(`first_name`, `password`, `email`) VALUES(%s, %s, %s)', (username, encrypted_password, email))
                    connection.commit()
                    msg = 'You have successfully registered!'
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            msg = 'Please fill out the form!'
        return render_template('register.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['first_name'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Connect to the database
    with create_connection() as connection:
        # Check if user is loggedin
        if 'loggedin' in session:
            # We need all the account info for the user so we can display it on the profile page
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM tblusers WHERE user_id = %s', (session['user_id'],))
                # Fetch one record and return result
                account = cursor.fetchone()
                if account['role_id'] == 0:
                    # Show the profile page with account info
                    return render_template('profile.html', account=account)
                elif account['role_id'] == 1:
                    cursor.execute('SELECT * FROM tblusers')
                    accounts = cursor.fetchall()
                    return render_template('admin.html', account=account, accounts=accounts)
        # User is not loggedin redirect to login page
        return redirect(url_for('login'))


@app.route('/pythonlogin/delete_users', methods=['GET', 'POST'])
def delete():
    user_id = request.args.get('user_id')
    # Connect to the database
    with create_connection() as connection:
        if request.method == "POST":
            # Delete code here
            with connection.cursor() as cursor:
                user_id = request.form['user_id']
                avatar = request.form['avatar']
                if avatar:
                    # Assuming the filename is the same as the user_id with a .jpg extension
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar)
                    print(image_path)

                    if os.path.exists(image_path):
                        os.remove(image_path)
                del_sql='''
                DELETE FROM tblusers WHERE user_id = %s
                ''' 
                val = user_id
                cursor.execute(del_sql,val)
                connection.commit()
                return redirect('/')
        with connection.cursor() as cursor:
            user_sql='''
            SELECT * from tblusers
            WHERE
            user_id = %s
            '''
            val = request.args.get('user_id')
            cursor.execute(user_sql,val)
            user = cursor.fetchone()
        return render_template('delete_users.html', user = user)

@app.route('/static/Images/blank-user.jpg')
def default_image():
    return send_file('./static/Images/blank-user.jpg', mimetype='image/jpg')

@app.route('/pythonlogin/update_users', methods=['GET', 'POST'])
def update():
    user_id = request.args.get('user_id')
    # Connect to the database
    with create_connection() as connection:
        if request.method == "POST":
            user_id = request.form['user_id']
            username = request.form['first_name']
            password = request.form['password']
            new_password = request.form['new_password']
            email = request.form['email']

            # Managing profile avatar upload
            if 'avatar' in request.files.keys():
                with connection.cursor() as cursor:
                    user_w_img = []
                    img_folder = []
                    number = None
                    msg4 = None 
                    avatar = request.files['avatar']
                    if avatar:
                        dir_path = r'./static/Images/'
                        for path in os.listdir(dir_path):
                            if os.path.isfile(os.path.join(dir_path, path)):
                                img_folder.append(path.strip('.'))
                        for obj in img_folder:
                            obj = obj.split(".")
                            del obj[-1]
                            number = obj[0]
                            obj = "".join(obj)
                            user_w_img.append(obj[1:])
                        print(img_folder, user_w_img)
                        num = str(random.randint(1,9))
                        while num == str(number):
                            num = str(random.randint(1,9))
                        if str(avatar.filename.split('.')[-1]) in ALLOWED_EXTENSIONS:
                            file = num + "." + str(session['user_id'])
                            filename = os.path.join(app.config["UPLOAD_FOLDER2"], "%s.%s" % (file, avatar.filename.split('.')[-1]))
                            if str(session['user_id']) not in user_w_img:
                                avatar.save(filename)
                                print("saved img")
                            else:
                                os.remove(dir_path + img_folder[user_w_img.index(str(session['user_id']))])
                                avatar.save(filename)
                                print("saved new img")
                            print(filename)
                            filename = filename.split("/")
                            filename = filename[-1]
                            print(filename)
                            # Update in database
                            cursor.execute("UPDATE tblusers SET avatar = %s WHERE user_id = %s",(filename, session['user_id']))
                        else:
                            msg4 = 'File extention is not valid! It should be in the format of .png, .jpg, .jpeg, jfif or .gif.' 
                            flash(msg4)

            # Update code here
            with connection.cursor() as cursor:
                user_id = request.form['user_id']
                msg = None
                msg2 = None
                msg3 = None
                if not re.match(r'[A-Za-z0-9]+', username):
                    msg = 'Username must contain only characters and numbers!'
                    flash(msg)
                if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                    msg2 = 'Invalid email address!'
                    flash(msg2)
                if new_password:
                    if re.match(r'[A-Za-z0-9]+', new_password):
                        password = hashlib.sha256(new_password.encode()).hexdigest()
                    elif not re.match(r'[A-Za-z0-9]+', new_password):
                        msg3 = 'Password must contain only characters and numbers!'
                        flash(msg3)
                if msg is None and msg2 is None and msg3 is None and msg4 is None:
                    user_sql = "UPDATE tblusers SET first_name=%s, email=%s, password=%s WHERE user_id = %s"
                    cursor.execute(user_sql, (username, email, password, user_id))
                    connection.commit()
                    return redirect('/pythonlogin/profile')
        with connection.cursor() as cursor:
            user_sql='''
            SELECT * from tblusers
            WHERE
            user_id = %s
            '''
            val = request.args.get('user_id')
            print(val)
            cursor.execute(user_sql, val)
            user = cursor.fetchone()

        return render_template('update_users.html', user = user)


@app.route('/pythonlogin/make_admin',methods=['POST'])
def make_admin():
    # Connect to the database
    with create_connection() as connection:
        with connection.cursor() as cursor:
                user_id = request.form['user_id']
                if user_id and request.method=="POST":
                    sql='''
                    UPDATE tblusers SET role_id = 1 WHERE user_id = %s
                    '''
                    val= user_id
                    cursor.execute( sql,val)
                    connection.commit()
                    cursor.close()
                    connection.close()
                    return redirect('/pythonlogin/profile')


@app.route('/pythonlogin/make_user',methods=['POST'])
def make_user():
    # Connect to the database
    with create_connection() as connection:
        with connection.cursor() as cursor:
                user_id = request.form['user_id']
                if user_id and request.method=="POST":
                    sql='''
                    UPDATE tblusers SET role_id = 0 WHERE user_id = %s
                    '''
                    val= user_id
                    cursor.execute( sql,val)
                    connection.commit()
                    cursor.close()
                    connection.close()
                    return redirect('/pythonlogin/profile')


@app.route("/pythonlogin/brag_board", methods=["GET", "POST"])
def brag_board():
    if request.method == "POST":
        # Add new message to database
        title = request.form["title"]
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        image = request.files["image"]  # Access the image using request.files
        brag = request.form["brag"]
        user_id = session["user_id"]  # Assuming user ID is stored in session

        # Managing image posting upload
        image_filename = ""
        if 'image' in request.files.keys():
            image = request.files['image']
            if image:
                if str(image.filename.split('.')[-1]) in ALLOWED_EXTENSIONS:
                    # Generate a unique filename for the post image
                    unique_filename = str(uuid.uuid4()) + "." + image.filename.split('.')[-1]
                    # Save the image to the post_images folder
                    image.save(os.path.join(UPLOAD_FOLDER2, unique_filename))

                    # Set the image filename for the post
                    image_filename = unique_filename
                else:
                    msg4 = 'File extension is not valid! It should be in the format of .png, .jpg, .jpeg, jfif, or .gif.'
                    flash(msg4)
                    return redirect(url_for('brag_board'))
        else:
            # Set the image filename to an empty string if there's no image
            image_filename = ""

        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO tblboard (title, date, brag, user_id, image) VALUES (%s, %s, %s, %s, %s)", (title, date, brag, user_id, image_filename))
                connection.commit()

        return redirect(url_for('brag_board'))  # Add this line to redirect after POST

    # Get all messages and accounts from database
    with create_connection() as connection:
        with connection.cursor() as cursor:
            # Fetch posts with likes and dislikes count
            cursor.execute("""
                SELECT
                    tblboard.*,
                    SUM(tblpostlikes.likes) AS likes_count,
                    SUM(tblpostlikes.dislikes) AS dislikes_count,
                    tblcomments.comment,
                    tblcomments.comment_date,
                    tblusers.first_name AS user_name
                FROM
                    tblboard
                LEFT JOIN tblpostlikes
                    ON tblboard.board_id = tblpostlikes.board_id
                LEFT JOIN tblcomments
                    ON tblboard.board_id = tblcomments.board_id
                LEFT JOIN tblusers
                    ON tblcomments.user_id = tblusers.user_id
                GROUP BY
                    tblboard.board_id,
                    tblcomments.comment_id
            """)
            tblboard = cursor.fetchall()

            cursor.execute("SELECT * FROM tblusers")
            accounts = cursor.fetchall()

    return render_template("brag_board.html", tblboard=tblboard, accounts=accounts, post={})  # Pass an empty dictionary as the default value for 'post'


@app.route('/pythonlogin/edit_post', methods=['POST'])
def edit_post():
    board_id = request.form['board_id']
    title = request.form['title']
    brag = request.form['brag']
    image = request.files.get('image')

    if not board_id or not title or not brag:
        return "Invalid input", 400

    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tblboard")
            tblboard = cursor.fetchall()
            
            image_filename = None

            if image:
                if str(image.filename.split('.')[-1]) in ALLOWED_EXTENSIONS:
                    unique_filename = str(uuid.uuid4()) + "." + image.filename.split('.')[-1]
                    # Before saving a new image, delete the old one
                    cursor.execute("SELECT image FROM tblboard WHERE board_id = %s", (board_id,))
                    result = cursor.fetchone()
                    old_image_filename = result["image"] if result else None
                    if old_image_filename:
                        old_image_filepath = os.path.join(app.config["UPLOAD_FOLDER2"], old_image_filename)
                        if os.path.exists(old_image_filepath):
                            os.remove(old_image_filepath)
                    # Save the new image
                    image.save(os.path.join(app.config["UPLOAD_FOLDER2"], unique_filename))
                    image_filename = unique_filename
                else:
                    return "Invalid image format", 400

            if image_filename:
                cursor.execute("UPDATE tblboard SET title=%s, brag=%s, image=%s WHERE board_id=%s", (title, brag, image_filename, board_id))
            else:
                cursor.execute("UPDATE tblboard SET title=%s, brag=%s WHERE board_id=%s", (title, brag, board_id))

            # fetch the updated post
            cursor.execute("SELECT * FROM tblboard WHERE board_id = %s", (board_id,))
            post = cursor.fetchone()

            # fetch the current user's account information
            cursor.execute("SELECT * FROM tblusers WHERE user_id = %s", (session['user_id'],))
            account = cursor.fetchone()

            connection.commit()

    return render_template(
        'brag_board.html',
        post=post,
        user_id=session['user_id'],
        role_id=session['role_id'],
        author_id=post['user_id'] if post else None,
        tblboard=tblboard
    )


@app.route("/pythonlogin/delete_post", methods=['GET', 'POST'])
def delete_post():
    board_id = request.args.get('board_id')

    # Connect to the database
    with create_connection() as connection:
        with connection.cursor() as cursor:
            if request.method == "POST":
                # Fetch the filename of the image associated with the post
                cursor.execute("SELECT image FROM tblboard WHERE board_id = %s", (board_id,))
                result = cursor.fetchone()
                image_filename = result["image"] if result else None

                # Delete the image file if it exists
                if image_filename:
                    image_filepath = os.path.join(app.config["UPLOAD_FOLDER2"], image_filename)
                    if os.path.exists(image_filepath):
                        os.remove(image_filepath)

                # Delete likes/dislikes associated with the post
                del_likes_sql = '''
                DELETE FROM tblpostlikes WHERE board_id = %s
                ''' 
                cursor.execute(del_likes_sql, (board_id,))

                # Then, delete the post itself
                del_sql = '''
                DELETE FROM tblboard WHERE board_id = %s
                ''' 
                cursor.execute(del_sql, (board_id,))
                
                connection.commit()
                
                return redirect('/pythonlogin/brag_board')

            # fetch the post
            board_sql = '''
            SELECT * from tblboard
            WHERE
            board_id = %s
            '''
            cursor.execute(board_sql, (board_id,))
            post = cursor.fetchone()

            # fetch the current user's account information
            cursor.execute("SELECT * FROM tblusers WHERE user_id = %s", (session['user_id'],))
            account = cursor.fetchone()
        
    return render_template(
        'brag_board.html',
        post=post,
        user_id=session['user_id'],
        role_id=session['role_id'],
        author_id=post['user_id'] if post else None
    )
   

@app.route("/pythonlogin/like_post", methods=["GET"])
def like_post():
    board_id = request.args.get("board_id")
    like = request.args.get("like", "false")  # default to "false" if "like" argument is not provided
    like = True if like.lower() == 'true' else False
    user_id = session["user_id"]

    if board_id is None:
        return "Invalid request: board_id is required", 400

    with create_connection() as connection:
        with connection.cursor() as cursor:
            # Check if a like or dislike already exists from this user
            cursor.execute(
                "SELECT * FROM tblpostlikes WHERE user_id = %s AND board_id = %s",
                (user_id, board_id)
            )
            existing_like = cursor.fetchone()

            if existing_like:
                if (existing_like["likes"] == 1 and like) or (existing_like["dislikes"] == 1 and not like):
                    # Remove like/dislike if the same button is clicked again
                    cursor.execute(
                        "DELETE FROM tblpostlikes WHERE user_id = %s AND board_id = %s",
                        (user_id, board_id)
                    )
                else:
                    # Update like to dislike or vice versa
                    cursor.execute(
                        "UPDATE tblpostlikes SET likes = %s, dislikes = %s WHERE user_id = %s AND board_id = %s",
                        (1 if like else 0, 0 if like else 1, user_id, board_id)
                    )
            else:
                print('interesting')
                try:
                    cursor.execute(
                        "INSERT INTO tblpostlikes (board_id, user_id, likes, dislikes) VALUES (%s, %s, %s, %s)",
                        (board_id, user_id, 1 if like else 0, 0 if like else 1)
                    )
                    print("INSERT INTO tblpostlikes (board_id, user_id, likes, dislikes) VALUES (%s, %s, %s, %s)" % (board_id, user_id, 1 if like else 0, 0 if like else 1))
                except IntegrityError:
                    cursor.execute(
                        "UPDATE tblpostlikes SET likes = %s, dislikes = %s WHERE user_id = %s AND board_id = %s",
                        (1 if like else 0, 0 if like else 1, user_id, board_id)
                    )
            
            connection.commit()

            # Fetch the updated like and dislike counts for this post
            cursor.execute("SELECT SUM(likes) as likes_count, SUM(dislikes) as dislikes_count FROM tblpostlikes WHERE board_id = %s", (board_id,))
            counts = cursor.fetchone()
        likes_count = 0 if counts["likes_count"] is None else int(counts["likes_count"])
        dislikes_count = 0 if counts["dislikes_count"] is None else int(counts["dislikes_count"])

    return jsonify({"likes": likes_count, "dislikes": dislikes_count})

@app.route('/pythonlogin/post_comment', methods=['POST'])
def post_comment():
    board_id = request.form['board_id']
    user_id = session['user_id']
    comment = request.form['comment']
    comment_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    print(comment_date, comment, user_id)

    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tblcomments (user_id, board_id, comment, comment_date) VALUES (%s, %s, %s, %s)",
                (user_id, board_id, comment, comment_date)
            )
            connection.commit()

            # Fetch the newly added comment
            cursor.execute(
                """
                SELECT tblcomments.*, tblusers.first_name as user_name 
                FROM tblcomments 
                LEFT JOIN tblusers ON tblcomments.user_id = tblusers.user_id 
                WHERE tblcomments.comment_id = LAST_INSERT_ID()
                """
            )
            new_comment = cursor.fetchone()

    # Convert the comment_date to a string
    new_comment["comment_date"] = new_comment["comment_date"].strftime('%Y-%m-%d %H:%M:%S')

    # Return the new comment as JSON response
    return jsonify(new_comment)


if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT,debug=False)