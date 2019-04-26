import os
import sys
import cv2

# path needs to be specified as argument
PATH = sys.argv[0]

FACE_CASCADE = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# multiple values by which to increase size of cropped face based on initial detection
# inserted because OpenCV tends to vary somewhat in terms of it's detection ranges
# using multiple sizes allows the user to manually review outputs and select suitable photos
EXPANSION_FACTORS = {
    ('SM', .35),
    ('LG', .25)
}


# value by which to slide crop window up or down
VERTICAL_OFFSET_FACTOR = -.005


# list PNG and JPG files in folder
FILES = []
for r, d, f in os.walk(PATH):
    for file in f:
        if ('.jpg' in file) or ('.png' in file):
            FILES.append(file)

# create subdirectory for cropped photos
if FILES:
    os.makedirs(PATH + '\\cropped', exist_ok=True)

for file in FILES:
    # load image from file and convert to grayscale for detection

    IMG = cv2.imread(PATH + '\\' + file)
    GRAY = cv2.cvtColor(IMG, cv2.COLOR_BGR2GRAY)

    # calc slide based on overall height of original image
    VERTICAL_OFFSET = int(GRAY.shape[0]*VERTICAL_OFFSET_FACTOR)

    # build array of detected face coordinates
    FACES = FACE_CASCADE.detectMultiScale(GRAY, scaleFactor=1.3, minNeighbors=5)

    # cycle through expansion options
    for (size, factor) in EXPANSION_FACTORS:

        # return coordinates of biggest face if multiple faces detected
        FACE_DIMENSION = 0
        for (x, y, w, h) in FACES:
            if w*h > FACE_DIMENSION:
                FACE_DIMENSION = w*h
                face_y = y-int(w*factor)+VERTICAL_OFFSET
                face_x = x-int(w*factor)
                face_h = int(w*(1+factor*2))
                face_w = int(w*(1+factor*2))

        # load found image
        CROPPED_IMG = IMG[face_y:face_y+face_w, face_x:face_x+face_h]
        # write to file
        cv2.imwrite(
            PATH +
            '\\cropped\\' +
            os.path.splitext(file)[0] +
            '_' +
            size +
            os.path.splitext(file)[1],
            CROPPED_IMG)
