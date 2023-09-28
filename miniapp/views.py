import smtplib
import sys
import numpy as np
# import os
# import cv2
# import time
import subprocess
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse,request
from django.urls import reverse
from django.shortcuts import render
import mysql.connector
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
# from django.contrib.auth import authenticate, login
from .models import Image, Online
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Create your views here.
def index(request):
    return render(request,'index.html')

def register(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="boardvir",
            port=3308
        )

        # Create a cursor
        mycursor = conn.cursor()

        query = "INSERT INTO online (first_name, last_name, email, password, confirm_password) VALUES (%s, %s, %s, %s, %s)"
        values = (first_name, last_name, email, password, confirm_password)
        mycursor.execute(query, values)


        # Commit the transaction
        conn.commit()

        # Close the cursor and the database connection
        mycursor.close()
        conn.close()

        return render(request, 'login.html', {"status": "you can login"})
    else:
        return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        email=request.POST['email']
        password=request.POST['password']
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="boardvir",
            port=3308
        )
        mycursor = conn.cursor()
        mycursor.execute("select * from online where email='"+email+"' and password='"+password+"'")
        result=mycursor.fetchone()
        if(result!=None):
            request.session["email"]=email
            return redirect('home')
        else:
            return render(request,"login.html",{"status":"invalid credentials"})
    else:
        return render(request,'login.html')   

def home(request):
    if("email" in request.session):
        print('in home')
        return render(request,'home.html')
    else:
        return render(request,'login.html')

def profile(request):
    return render(request,'profile.html')

def logout(request):
    print('logout')
    del request.session["email"]
    return redirect('login')

def code_execution_view(request):
    print('in code execution view')
    if("email" not in request.session):
        print('in if')
        return  redirect('login')
    
    save_counter = request.session.get('save_counter', 0)
    if request.method == 'POST':
        default_code = '''

import numpy as np
import time
import cv2
import mediapipe as mp
import mysql.connector
import os

print("Importing done")

cap = cv2.VideoCapture(0)

frameWidth = 640
frameHeight = 480
cap.set(3, frameWidth)
cap.set(4, frameHeight)
cap.set(10, 150)
prevx = 0
prevy = 0
cx = 0
cy = 0
ix = 0
iy = 0
jx = 0
jy = 0

board = np.zeros((frameHeight, frameWidth, 3), dtype=np.uint8)
board_bg = np.zeros((frameHeight, frameWidth, 3), dtype=np.uint8)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

pTime = 0
cTime = 0

save_counter = 0  # Initialize a counter for saved images


def distance(ix, jx, iy, jy):
    dista = ((ix - jx) * (ix - jx) + (iy - jy) * (iy - jy))
    return int(dista)


while True:
    cx = 0
    cy = 0
    ix = 0
    iy = 0
    jx = 0
    jy = 0
    board_pointer = np.zeros((frameHeight, frameWidth, 3), dtype=np.uint8)
    success, img = cap.read()
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                if id == 8:
                    ix = cx
                    iy = cy
                    cv2.circle(board_pointer, (ix, iy),
                            5, (0, 0, 255), cv2.FILLED)
                if id == 4:
                    jx = cx
                    jy = cy
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    dist = distance(ix, jx, iy, jy)
    if ix and jx:
        if dist < 1000:
            cv2.line(board_bg, (prevx, prevy), (ix, iy), (0, 255, 0), 5)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('x'):
        board_bg = np.zeros((frameHeight, frameWidth, 3), dtype=np.uint8)
        print('Allclear')
    if key == ord('s'):
        print('Save is Clicked')
        save_counter += 1
        save_directory = "/Users/saieshwarrampelli/mini10/media/"  # Set your desired directory
        filename = f"board_{save_counter}_{time.strftime('%Y%m%d%H%M%S')}.png"
        
        # Full path to save the image
        full_path = os.path.join(save_directory, filename)
        
        cv2.imwrite(full_path, board_bg)
        print(f"Board saved as {filename}")
        
        # Extract only the filename (without the path) for database insertion
        filename_only = os.path.basename(full_path)
        
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="boardvir",
            port=3308
        )
        mycursor = conn.cursor()
        
        # Insert only the filename into the database
        mycursor.execute("INSERT INTO collections (imagename) VALUES (%s)", (filename_only,))
        conn.commit()

    if key == 27:
        print('Exit')
        break
    cv2.putText(img, str(int(fps)), (10, 70),
                cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
    prevx = ix
    prevy = iy
    board = board_bg + board_pointer
    cv2.imshow("Image", img)
    cv2.imshow("Board", board)

cap.release()
cv2.destroyAllWindows()



'''
        python_executable = sys.executable


        try:
            result = subprocess.check_output([python_executable, '-c', default_code], stderr=subprocess.STDOUT, text=True)
            return render(request, 'collection.html', {'status': 'stored successfully'})
        except subprocess.CalledProcessError as e:
            return JsonResponse({'output': e.output})

    # Get the URL of the code execution view
    code_execution_url = reverse('runcode')

    return render(request, 'home.html', {'code_execution_url': code_execution_url})

def runcode_view(request):
    # Placeholder view, you can implement your code execution logic here.
    return render(request, 'home.html')


def collection(request):
    conn=mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="",
                database="boardvir",
                port=3308
            )
    mycursor=conn.cursor()
    mycursor.execute("select * from collections")
    result=mycursor.fetchall()
    images=[]
    if(result!=None):
        for x in result:
            s=Image()
            s.imageid=x[0]
            s.imagename=x[1]
            images.append(s)
    return render(request,'collection.html',{"images":images,"MEDIA_URL":settings.MEDIA_URL})

def profile(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email=request.POST['email']
        password=request.POST['password']
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="boardvir",
            port=3308
        )
        mycursor = conn.cursor()
        mycursor.execute("select * from online where email='"+email+"' and password='"+password+"'")
        result=mycursor.fetchone()
        if(result!=None):
            request.session["email"]=email
            return redirect('home')
        else:
            return render(request,"login.html",{"status":"invalid credentials"})
    else:
        return render(request,'login.html')
    
def profile(request):
    if("email" not in request.session):
        redirect('login')
    email=request.session["email"]
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="boardvir" , 
        port=3308      
        )
    mycursor = conn.cursor()
    mycursor.execute("select * from online where email='"+email+"'")
    result=mycursor.fetchall()
    online=[]
    if(result!=None):
        for x in result:
            c=Online()
            c.id=x[0]
            c.first_name=x[1]
            c.last_name=x[2]
            c.email=x[3]
            c.password=x[4]
            online.append(c)
        return render(request,'profile.html',{"online":online})
    else:
        return render(request,'login.html')  


def forgotpassword(request):
    if request.method == 'POST':
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="boardvir",
            port=3308
        )
        mycursor = conn.cursor()
        # retrieve post details
        email = request.POST['email']
        mycursor.execute(
            "SELECT password FROM online WHERE email='" + email + "'")
        result = mycursor.fetchone()
        pwd = str(result)
        if result is not None:
            # SMTP server configuration
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
            smtp_username = 'rampallisaieshwar@gmail.com'
            # For App Password, enable 2-step verification, then create an app password
            smtp_password = 'ruohgfxtavyzucco'
            # Email content
            subject = 'Password recovery'
            body = 'This is a Password recovery email sent from VR. ' \
                   'Your password as per registration is: ' + pwd[2:len(pwd) - 3]
            sender_email = 'rampallisaieshwar@gmail.com'
            receiver_email = email
            # Create a message
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = receiver_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            # Connect to SMTP server and send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            message = "Password sent to the given email ID"
            return render(request, 'login.html', {'alert_message': message})
        else:
            message = "Please enter the correct email ID"
            return render(request, 'forgotpassword.html', {'alert_message': message})
    else:
        return render(request, 'forgotpassword.html')


def button_action(request):
    message = "We Received your Response. We'll get back to you soon...."
    return render(request, 'home.html', {'alert_message': message})

def contact(request):
    if request.method == 'POST':
        # Get form data
        your_name = request.POST['full-name']  
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']

        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="boardvir",
            port=3308
        )

        # Create a cursor
        mycursor = conn.cursor()

        query = "INSERT INTO contact (your_name, email, subject, message) VALUES (%s, %s, %s, %s)"  # Remove the extra %s
        values = (your_name, email, subject, message)
        mycursor.execute(query, values)

        # Commit the transaction
        conn.commit()

        # Close the cursor and the database connection
        mycursor.close()
        conn.close()
        return HttpResponse("Success! Form submitted")  
    else:
        return render(request, 'contact.html')
