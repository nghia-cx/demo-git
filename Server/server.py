# from importlib.resources import path
import socket
import numpy as np
import cv2
from Crypto.Cipher import AES

HOST='192.168.1.2'
PORT=9000
WIDTH = 960
HEIGHT = 540
import os
import glob
import time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)


def recv_all(sc, length):
    data = sc.recv(length)
    while True:
        miss_len_data = length - len(data)
        if miss_len_data==0:
            break
        data += sc.recv(miss_len_data)
    return data
  # ****** AES **********
def generateAESKey(key_string, len_key):
    '''Generate 128/192/256 bit key from from any key'''
    key = bytes(key_string,"utf8")
    while len(key)<len_key:
        key = key + key
    return key[:len_key]

def encode_AES(data, key):

    cipher = AES.new(key, AES.MODE_ECB)
    # Mã hóa 
    ciphertext = cipher.encrypt(data)
    return ciphertext

def decode_AES(data_enc, key): # decode AES
    cipher = AES.new(key, AES.MODE_ECB)
    plaintext = cipher.decrypt(data_enc)
    return plaintext

def make_folder(folder_name):
    if os.path.isdir(os.path.dirname(__file__)+"/"+folder_name) == False:
        os.mkdir(os.path.dirname(__file__)+"/"+folder_name)
    list_folder = glob.glob(os.path.dirname(__file__)+"/"+folder_name+"/*")
    max=0
    for i in list_folder:
        try:
            num = int(i.split("-")[1])
            if(max<num): max = num
        except: continue
    path = os.path.dirname(__file__)+"/"+folder_name+"/data-"+str(max+1)
    os.mkdir(path)
    return path

# connect to client
def connect(s):
    print("Connecting...")
    while True:
        try: 
            client, addr = s.accept()
            print('Connected by', addr)
            break
        except:
            print("Run Client.py, Please")
    return client, addr
    
# Menu

def sendImage(client,key_AES):
    
    print("waiting for your camera...")
    vid = cv2.VideoCapture(0)
    
    # capture image
    while True:
        rate,frame = vid.read() #read image from camera
        if not rate: continue
        frame = cv2.resize(frame,(WIDTH,HEIGHT)) # resize image        
        if cv2.waitKey(1) & 0xFF == ord(' '): 
            # create folder
            save_path = make_folder("Images")
            cv2.imwrite(save_path+"/The-original-image.bmp",frame) # save image
            cv2.destroyWindow("Camera")
            cv2.imshow("Image",frame) # show image
            print("Took photos!")
            break
        frame = cv2.putText(frame, "Press 'space' to take a photo", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
        cv2.imshow("Camera",frame) # show image

    print("Waiting for Client... ")
    resp1 = recv_all(client,5) # wait client response
    if resp1 !=b"ready":
        print("Error.")
        return
    client.send(b"ready")
    
    # encode image
    st_time = time.time()
    im_byte = np.array(frame).tobytes() # image -> bytes
    data_enc = encode_AES(im_byte, key_AES) # encode AES
    enc_time = time.time()
    print(" - Encoded AES-%d (%.3f seconds)" %(8*len(key_AES),enc_time-st_time))


    # Send data
    print(" - Sending data to client...")
    client.send(data_enc) # send encoded data 

    recv_all(client,4) # wait server response
    send_time = time.time() 
    print("   Client has received data! " )
    f_data_enc = open(save_path+"/Data-sent-to-client.enc", "wb")
    f_data_enc.write(data_enc)
    f_data_enc.close()

    # Image encoded
    data_enc = np.frombuffer(data_enc, dtype = np.uint8)   #encoded data -> array
    data_enc = data_enc.reshape(HEIGHT, WIDTH, 3) # array encoded-> encoded image 
    cv2.imshow("Image encoded",data_enc) # show encoded image
    cv2.imwrite(save_path+"/AES-encrypted-image.bmp", data_enc)
    print("Done!")
    cv2.waitKey(0)

        
if __name__ == "__main__":

    print("Enter key: ")
    key=str(input())
    # key ="a"
    print("Choose cipher type:")
    print("1. AES-128")
    print("2. AES-192")
    print("3. AES-256")
    print("*Node: if you choose the wrong type of cipher this program will still run but the information you get will NOT be correct")
    print("Enter a number (1-3): ",end="")
    len_key=int(input())
    # len_key = 1
    len_key = 8 + len_key*8 
    key_AES = generateAESKey(key,len_key) # create AES key
    print("Your AES key: ", key_AES)

    client, addr = connect(s) # connect
    
    while True:
        print("------  MENU --------")
        print("1: Transmit images ")
        print("2: Chose another key")
        print("3: End")
        print("Enter a number (1-3): ",end="")
        x=int(input())
        # x=2
        if x==1:
            sendImage(client, key_AES)
        elif x==2:
            print("Enter key: ")
            key=str(input())
            key_AES = generateAESKey(key,len_key) # create AES key
            print("Your AES key: ", key_AES)
        elif x==3:
            print("END")
            break
    client.close()
