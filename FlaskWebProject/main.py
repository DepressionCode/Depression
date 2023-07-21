from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from datetime import datetime
from pymysql.err import IntegrityError
import pymysql
import re
import os
import arrow
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
        date_now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
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
                cursor.execute("INSERT INTO tblboard (title, date, brag, user_id, image) VALUES (%s, %s, %s, %s, %s)", (title, date_now, brag, user_id, image_filename))
                connection.commit()

        return redirect(url_for('brag_board'))  # Add this line to redirect after POST

    # Get all messages and accounts from database
    with create_connection() as connection:
        with connection.cursor() as cursor:
            # Fetch posts with likes and dislikes count
            cursor.execute("""
                SELECT
                    tblboard.*,
                    tblusers.first_name AS user_name,
                    COALESCE(SUM(tblpostlikes.likes), 0) as likes_count,
                    COALESCE(SUM(tblpostlikes.dislikes), 0) as dislikes_count
                FROM
                    tblboard
                LEFT JOIN tblusers
                    ON tblboard.user_id = tblusers.user_id
                LEFT JOIN tblpostlikes
                    ON tblboard.board_id = tblpostlikes.board_id
                GROUP BY
                    tblboard.board_id,
                    tblusers.user_id
                ORDER BY tblboard.date DESC
            """)
            posts = cursor.fetchall()

            for post in posts:
                cursor.execute("""
                    SELECT
                        tblcomments.comment_id,
                        tblcomments.comment,
                        tblcomments.comment_date,
                        tblusers.first_name AS user_name,
                        tblcomments.user_id AS user_id
                    FROM
                        tblcomments
                    LEFT JOIN tblusers
                        ON tblcomments.user_id = tblusers.user_id
                    WHERE
                        tblcomments.board_id = %s
                """, (post["board_id"],))
                comments = cursor.fetchall()
                
                for comment in comments:
                    # Set the can_delete flag for each comment
                    comment['can_delete'] = comment['user_id'] == session["user_id"]

                post["comments"] = comments

                # Fetch likes and dislikes
                cursor.execute("""
                    SELECT
                        SUM(likes) AS likes_count,
                        SUM(dislikes) AS dislikes_count
                    FROM
                        tblpostlikes
                    WHERE
                        tblpostlikes.board_id = %s
                """, (post["board_id"],))
                likes_dislikes = cursor.fetchone()
                post["likes"] = likes_dislikes["likes_count"] or 0
                post["dislikes"] = likes_dislikes["dislikes_count"] or 0
                date_now = datetime.now()
                d = str(post['date'])
                date_in_db = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')

                # Calculate time difference
                diff = date_now - date_in_db

                # Get difference in minutes
                diff_minutes = diff.total_seconds() / 60
                if diff_minutes < 60:
                    post['date'] = str(int(diff_minutes)) + " minutes ago"
                elif 60 <= diff_minutes < 60 * 24:
                    # Change it to hours if difference is 60 minutes or more
                    diff_hours = diff_minutes / 60
                    post['date'] = str(int(diff_hours)) + " hours ago"
                elif 60 * 24 <= diff_minutes < 60 * 24 * 365:
                    # Change it to days if difference is 24 hours or more
                    diff_days = diff_minutes / 60 / 24
                    post['date'] = str(int(diff_days)) + " days ago"
                else:
                    # Change it to years if difference is 365 days or more
                    diff_years = diff_minutes / 60 / 24 / 365
                    post['date'] = str(int(diff_years)) + " years ago"

            # Fetch users
            cursor.execute("SELECT * FROM tblusers")
            accounts = cursor.fetchall()

            # Fetch the current user's data
            cursor.execute("SELECT * FROM tblusers WHERE user_id = %s", (session["user_id"],))
            user = cursor.fetchone()

    post = {}  # Initialize post as an empty dictionary

    return render_template("brag_board.html", tblboard=posts, accounts=accounts, data=user, post=post)


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

            connection.commit()

            # fetch the updated post
            cursor.execute("SELECT * FROM tblboard WHERE board_id = %s", (board_id,))
            post = cursor.fetchone()

            # fetch the current user's account information
            cursor.execute("SELECT * FROM tblusers WHERE user_id = %s", (session['user_id'],))
            account = cursor.fetchone()

    with create_connection() as connection:
        with connection.cursor() as cursor:
            # fetch the updated tblboard data
            cursor.execute("SELECT * FROM tblboard")
            tblboard = cursor.fetchall()

    return render_template(
        'brag_board.html',
        post=post,
        user_id=session['user_id'],
        role_id=session['role_id'],
        author_id=post['user_id'] if post else None,
        tblboard=tblboard,
        data=account 
    )



@app.route("/pythonlogin/delete_post", methods=['GET', 'POST'])
def delete_post():
    board_id = request.args.get('board_id')

    # Connect to the database
    with create_connection() as connection:
        with connection.cursor() as cursor:
            # fetch the post
            board_sql = '''
            SELECT * from tblboard
            WHERE
            board_id = %s
            '''
            cursor.execute(board_sql, (board_id,))
            post = cursor.fetchone()

            # check if the post exists
            if post is None:
                flash("Post not found.")
                return redirect('/pythonlogin/brag_board')

            # check if the user is allowed to delete the post
            if session['user_id'] != post['user_id'] and session['role_id'] != 1:
                flash("You are not authorized to delete this post.")
                return redirect('/pythonlogin/brag_board')

            if request.method == "POST":
                # Fetch the filename of the image associated with the post
                image_filename = post["image"]

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

                flash("Post successfully deleted.")
                return redirect('/pythonlogin/brag_board')

            # fetch the current user's account information
            cursor.execute("SELECT * FROM tblusers WHERE user_id = %s", (session['user_id'],))
            account = cursor.fetchone()

            # fetch the updated tblboard data
            cursor.execute("SELECT * FROM tblboard")
            tblboard = cursor.fetchall()

    return render_template(
        'brag_board.html',
        post=post,
        user_id=session['user_id'],
        role_id=session['role_id'],
        author_id=post['user_id'] if post else None,
        tblboard=tblboard
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


@app.route('/pythonlogin/add_comment', methods=['POST'])
def add_comment():
    connection = create_connection()  # Initialize the connection variable

    try:
        comment = request.form['comment']
        comment_id = request.form.get('comment_id')
        comment_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        board_id = request.form['board_id']
        user_id = session['user_id']

        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO tblcomments (comment, comment_id, comment_date, board_id, user_id) VALUES (%s, %s, %s, %s, %s)", (comment, comment_id, comment_date, board_id, user_id))
            connection.commit()

            # Fetch the comment that was just inserted, along with the user's name
            cursor.execute("""
                SELECT
                    tblcomments.*,
                    tblusers.first_name AS user_name,
                    tblusers.user_id AS user_id
                FROM
                    tblcomments
                LEFT JOIN tblusers
                    ON tblcomments.user_id = tblusers.user_id
                WHERE
                    tblcomments.comment_id = %s
            """, (cursor.lastrowid,))
            new_comment = cursor.fetchone()

        # Return the new comment as JSON
        return jsonify(new_comment)

    finally:
        if connection:
            connection.close()


@app.route('/pythonlogin/delete_comment', methods=['POST'])
def delete_comment():
    print(request.form)  # let's print the entire form data
    comment_id = request.form.get('comment_id')

    print(comment_id)

    app.logger.info(f"Received delete_comment request. comment_id: {comment_id}")

    if not comment_id:
        app.logger.error("Invalid input: comment_id is missing")
        return "Invalid input", 400

    with create_connection() as connection:
        with connection.cursor() as cursor:
            # Fetch the comment to check if it exists and get the associated board_id
            cursor.execute("SELECT * FROM tblcomments WHERE comment_id = %s", (comment_id))
            comment = cursor.fetchone()

            if not comment:
                return "Comment not found", 404

            # Check if the user is authorized to delete the comment
            if session['user_id'] != comment['user_id']:
                return "Unauthorized", 403

            # Delete the comment
            cursor.execute("DELETE FROM tblcomments WHERE comment_id = %s", (comment_id))
            connection.commit()

    return "Comment successfully deleted"


@app.route('/pythonlogin/edit_comment', methods=['POST'])
def edit_comment():
    comment_id = request.form.get('comment_id')
    new_comment = request.form.get('new_comment')  # Changed variable name to new_comment

    print(comment_id)

    app.logger.info(f"Received edit_comment request. comment_id: {comment_id}, comment: {new_comment}")  # Changed variable name to new_comment

    if not comment_id or not new_comment:  # Changed variable name to new_comment
        app.logger.error("Invalid input: comment_id or comment is missing")
        return "Invalid input", 400

    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tblcomments WHERE comment_id = %s", (comment_id))
            existing_comment = cursor.fetchone()  # Changed variable name to existing_comment

            if not existing_comment:  # Changed variable name to existing_comment
                return "Comment not found", 404

            if session['user_id'] != existing_comment['user_id']:  # Changed variable name to existing_comment
                return "Unauthorized", 403

            cursor.execute("UPDATE tblcomments SET comment = %s WHERE comment_id = %s", (new_comment, comment_id))  # Changed variable name to new_comment
            connection.commit()

    return "Comment successfully updated"


if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT,debug=False)