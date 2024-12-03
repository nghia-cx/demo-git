import socket
# from tarfile import LENGTH_NAME
import numpy as np
import cv2
from Crypto.Cipher import AES

HOST='192.168.1.2'
PORT=9000
DATA_MAX = 2**24
WIDTH = 960
HEIGHT = 540
import os
import glob
import time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, PORT)

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
# Menu
    
def RecvImage(sc, key_AES):
    print("Waiting for Server...")

    # create folder to save data
    save_path = make_folder("Images")
    
    len_data = HEIGHT*WIDTH*3 #size of a frame

    sc.send(b"ready")

    resp1 = recv_all(sc,5)
    if resp1 !=b"ready":
        print("Error.")
        return
    

    s_time = time.time()
    data_enc = recv_all(sc, len_data) # receive data    
    sc.send(b"Done")
    # Save Data
    f_data_enc = open(save_path+"/Data-received-from-server.enc", "wb")
    f_data_enc.write(data_enc)
    f_data_enc.close()
    rec_time = time.time()
    print(" - Received data: %d KB (%.3f seconds)" %(int(len(data_enc)/1024),rec_time-s_time))

    # Save Image befor AES-decode    
    data_after_dec = np.frombuffer(data_enc, dtype = np.uint8)   #encoded data -> array
    data_after_dec = data_after_dec.reshape(HEIGHT, WIDTH, 3) # array encoded-> encoded image
    cv2.imwrite(save_path+"/image-before-decryption.bmp", data_after_dec)
    save_img_time = time.time()
    #Decode AES
    img_de = decode_AES(data_enc, key_AES) # decode AES
    img_de = np.frombuffer(img_de,dtype = np.uint8) # byte to array
    img_de = img_de.reshape(HEIGHT, WIDTH, 3) # array to image
    aes_time =  time.time()
    print(" - Decoded AES. (%.3f seconds)" %(aes_time-save_img_time))
    # Save Image after AES-decode
    cv2.imwrite(save_path + "/AES-decrypted-image" + ".bmp",img_de)
    print("The data has been saved to the path: %s" %save_path)
    print("Done!")
    cv2.imshow("AES decrypted image",img_de) # show decoded data
    cv2.waitKey(0)

def connect(sc):
    print("Connecting...")
    print("Waiting server...")
    while True:
        try:
            sc.connect(server_address)
            break
        except:
            ()
    return sc
   

if __name__ == "__main__":
    

    print("Enter key: ")
    key = str(input())
    # key = "a"
    print("Choose cipher type:")
    print("1. AES-128")
    print("2. AES-192")
    print("3. AES-256")
    print("*Node: if you choose the wrong type of cipher this program will still run but the information you get will NOT be correct")
    print("Enter a number (1-3): ",end="")
    len_key=int(input())
    # len_key=1
    len_key = 8 + len_key*8
    key_AES = generateAESKey(key,len_key)
    print("Your AES key: ", key_AES)

    s = connect(s)
    
    while True:
        print("------  MENU --------")
        print("1: Transmit images ")
        print("2: Chose another key")
        print("3: End")
        print("Enter a number (1-3): ",end="")
        x=int(input())
        # x=2
        if x==1:
            RecvImage(s, key_AES)
        elif x==2:
            print("Enter key: ")
            key=str(input())
            key_AES = generateAESKey(key,len_key) # create AES key
            print("Your AES key: ", key_AES)
        elif x==3:
            print("END")
            break 
    s.close()
