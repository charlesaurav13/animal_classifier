import email,os
from unittest import result
from pymongo import MongoClient
import random
import math
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask,flash, render_template, request,redirect, url_for
import requests as r
from werkzeug.utils import secure_filename
from lobe import ImageModel
import wikipediaapi



def generate_otp():
    digits = [i for i in range(0, 10)]
    global otp_code
    random_str = ""
    for i in range(6):
        index = math.floor(random.random()*10)
        random_str += str(digits[index])
    otp_code = random_str
    return random_str


def send_mail(receiver_mail, message):
    sender_email = "Your gmail"
    password = "Your password"
    msg = MIMEMultipart()
    msg["Subject"] = "Email Authentication"
    msg["From"] = "Your gmail"
    msg["To"] = "Your gmail"
    message1 = '''Dear User,
    Thank you for visting our website.Use the following OTP to complete your Sign Up procedures. OTP is valid for 5 minutes   '''
    body = message1 + str(message)
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_mail, text)
    server.quit()


app = Flask(__name__)

UPLOAD_FOLDER = 'static/images/uploads/'
 
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
def show():
    return render_template("login_logout.html")


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        if request.form['signin'] == 'signin':
            send_usermail = request.form['signemail']
            send_password = request.form['signpassword']
            cluster = MongoClient(
                "mongodb+srv://sahilshukla:Shuklaji123@cluster0.aplqu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
            db = cluster["detailsdb"]
            collection = db["loginDetails"]
            post = {"name": send_usermail, "password": send_password}
            collection.insert_one(post)
            results = collection.find({"name": send_usermail})
            return render_template("homepage.html")
        if request.form['signin'] == 'signup':
            send_username = request.form['username']
            send_email = request.form['email']
            send_signpass = request.form['password']
            cluster =MongoClient(
                "mongodb+srv://sahilshukla:Shuklaji123@cluster0.aplqu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
            db = cluster["detailsdb"]
            collection = db["loginDetails"]
            post = {"username": send_username,"email":send_email,"password":send_signpass}
            collection.insert_one(post)
            return render_template("index.html")
    return render_template("homepage.html")

    

@app.route('/email_otp', methods=['GET', 'POST'])
def email_authentication():
    global email
    email = request.form['email']
    send_mail(email, generate_otp())
    return render_template("email_otp.html", user_email=email)


@app.route('/resend_otp', methods=['GET', 'POST'])
def otp_resend():
    send_mail(email, generate_otp())
    return render_template("email_otp.html", user_email=email, resend_notice="Sending the otp Again")


@app.route('/success', methods=['GET', 'POST'])
def success():
    return render_template("homepage.html")


@app.route('/validate', methods=['POST'])
def validate():
    otp_got_from_website = request.form['number1']
    if int(otp_code) == int(otp_got_from_website):
        return render_template("homepage.html")

    return render_template("email_otp.html", msg="Not verified try Again:(",user_email=email)


@app.route('/index')
def login():
    return render_template("index.html")


@app.route('/search')
def search():
    return render_template("search.html")

# @app.route('/search',methods= ['POST'])
# def predict_default():
#     return render_template("search.html")


@app.route('/predict',methods= ['POST'])
def predict():
    if request.form['submit'] == 'file':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)
        
        model = ImageModel.load("model")
        given_path = r"static\images\uploads"
        file_path_from_file = os.path.join(given_path,filename)

        result = model.predict_from_file(file_path_from_file)
        for label, confidence in result.labels:
        #  added condition such that only some contents are visible
            if int(confidence*100) > 50:
                # print(f"{label}: {confidence*100}%")
                global name,name_confidence
                name = label
                name_confidence = confidence*100
    
    if request.form['submit'] =='url':
        got_url = request.form['get_url']
        get_response=r.get(got_url)
        global image_name
        image_name=got_url.split("/")[-1]
        os.chdir('static/images/uploads/')
        with open(image_name,"wb") as file_output:
            file_output.write(get_response.content)
            file_output.close()
        for i in range(1,4):
            os.chdir('..')
        model = ImageModel.load("model")
        result = model.predict_from_url(got_url)
        for label, confidence in result.labels:
        #  added condition such that only some contents are visible
            if int(confidence*100) > 50:
                # print(f"{label}: {confidence*100}%")
                name = label
                name_confidence = confidence*100
        wiki_wiki = wikipediaapi.Wikipedia('en')
        page_py = wiki_wiki.page(name)
        global summary
        summary = page_py.summary[0:680]
        return render_template("content.html",name = name,image_name = image_name, confidence = "{:.2f}".format(name_confidence))


    
    
    
    
    
    
    wiki_wiki = wikipediaapi.Wikipedia('en')
    page_py = wiki_wiki.page(name)
    summary = page_py.summary[0:680]
    return render_template("content.html",name = name,filename = filename,confidence = "{:.2f}".format(name_confidence))


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='images/uploads/' + filename), code=301)


@app.route('/display/<image_name>')
def display_image_url(image_name):
    return redirect(url_for('static', filename='images/uploads/' + image_name), code=301)



@app.route('/summary')
def summary():
    return render_template("summary.html",summary = summary,name = name.capitalize())


@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")



if __name__ == "__main__":
    app.run(debug=True)
