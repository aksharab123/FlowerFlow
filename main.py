import cv2
import mediapipe as mp
import os
import glob
import random
import math
import time
import pygame


# ============================================================
# FLOWERFLOW
# TWO HAND TRACKING + FLOWER TRAIL + FAST SWIRL SCATTER
# + WHITE/GOLD SPARKLES + MAGICAL AUDIO
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "hand_landmarker.task"
)

FLOWER_FOLDER = os.path.join(
    BASE_DIR,
    "assets",
    "flowers"
)

FORMATION_SOUND = os.path.join(
    BASE_DIR,
    "formation.mp3"
)

SCATTER_SOUND = os.path.join(
    BASE_DIR,
    "scatter.mp3"
)


# ============================================================
# AUDIO
# ============================================================

pygame.mixer.init()

formation_sound = None
scatter_sound = None

if os.path.exists(FORMATION_SOUND):
    formation_sound = pygame.mixer.Sound(
        FORMATION_SOUND
    )
    formation_sound.set_volume(0.55)
    print("Formation sound loaded.")

else:
    print("WARNING: formation.mp3 not found.")


if os.path.exists(SCATTER_SOUND):
    scatter_sound = pygame.mixer.Sound(
        SCATTER_SOUND
    )
    scatter_sound.set_volume(0.70)
    print("Scatter sound loaded.")

else:
    print("WARNING: scatter.mp3 not found.")


formation_channel = pygame.mixer.Channel(0)
scatter_channel = pygame.mixer.Channel(1)

formation_playing = False


# ============================================================
# LOAD FLOWERS
# ============================================================

flower_files = []

for ext in ["*.png", "*.jpg", "*.jpeg"]:

    flower_files += glob.glob(
        os.path.join(
            FLOWER_FOLDER,
            ext
        )
    )


flowers = []

for file in flower_files:

    image = cv2.imread(
        file,
        cv2.IMREAD_UNCHANGED
    )

    if image is not None:

        flowers.append(image)


print(
    "Flowers loaded:",
    len(flowers)
)


if len(flowers) == 0:

    print(
        "ERROR: No flowers found!"
    )

    print(
        FLOWER_FOLDER
    )

    pygame.quit()

    exit()


# ============================================================
# MEDIAPIPE
# ============================================================

BaseOptions = mp.tasks.BaseOptions

HandLandmarker = (
    mp.tasks.vision.HandLandmarker
)

HandLandmarkerOptions = (
    mp.tasks.vision.HandLandmarkerOptions
)

RunningMode = (
    mp.tasks.vision.RunningMode
)


options = HandLandmarkerOptions(

    base_options=BaseOptions(

        model_asset_path=MODEL_PATH

    ),

    running_mode=RunningMode.VIDEO,

    # TWO HANDS
    num_hands=2,

    min_hand_detection_confidence=0.45,

    min_hand_presence_confidence=0.45,

    min_tracking_confidence=0.45
)


# ============================================================
# PARTICLES
# ============================================================

particles = []

sparkles = []


# ============================================================
# FLOWER
# ============================================================

class Flower:

    def __init__(
        self,
        x,
        y
    ):

        self.image = random.choice(
            flowers
        )

        self.x = float(x)

        self.y = float(y)


        # ----------------------------------------------------
        # NORMAL MOVEMENT
        # ----------------------------------------------------

        self.vx = random.uniform(
            -0.2,
            0.2
        )

        self.vy = random.uniform(
            -0.2,
            0.2
        )


        # ----------------------------------------------------
        # SIZE
        # ----------------------------------------------------

        self.size = random.randint(
            28,
            55
        )


        # ----------------------------------------------------
        # LIFE
        # ----------------------------------------------------

        self.life = 1.0

        self.fade_speed = random.uniform(
            0.003,
            0.006
        )


        # ----------------------------------------------------
        # FLOATING
        # ----------------------------------------------------

        self.float_phase = random.uniform(
            0,
            math.pi * 2
        )

        self.float_speed = random.uniform(
            1.5,
            3.5
        )

        self.float_amount = random.uniform(
            0.2,
            0.8
        )


        # ----------------------------------------------------
        # ROTATION
        # ----------------------------------------------------

        self.angle = random.uniform(
            -15,
            15
        )

        self.rotation_speed = random.uniform(
            -0.25,
            0.25
        )


        # ----------------------------------------------------
        # SCATTER
        # ----------------------------------------------------

        self.scattering = False


# ============================================================
# SPARKLE
# ============================================================

class Sparkle:

    def __init__(
        self,
        x,
        y,
        golden=False
    ):

        self.x = float(x)

        self.y = float(y)


        # Small movement

        self.vx = random.uniform(
            -0.7,
            0.7
        )

        self.vy = random.uniform(
            -0.7,
            0.7
        )


        # Life

        self.life = 1.0

        self.fade_speed = random.uniform(
            0.015,
            0.035
        )


        # Small size

        self.size = random.uniform(
            0.8,
            2.0
        )


        self.phase = random.uniform(
            0,
            math.pi * 2
        )


        # ----------------------------------------------------
        # GOLD OR WHITE
        # ----------------------------------------------------

        self.golden = golden


# ============================================================
# ADD FLOWER
# ============================================================

def add_flower(
    x,
    y
):

    flower = Flower(

        x + random.uniform(
            -7,
            7
        ),

        y + random.uniform(
            -7,
            7
        )

    )

    particles.append(
        flower
    )


# ============================================================
# ADD WHITE + GOLD SPARKLES
# ============================================================

def add_sparkles(
    x,
    y
):

    # Keep trail sparkles subtle

    if random.random() > 0.22:

        return


    # Mostly white

    sparkle = Sparkle(

        x + random.uniform(
            -12,
            12
        ),

        y + random.uniform(
            -12,
            12
        ),

        golden=(
            random.random() < 0.30
        )

    )


    sparkles.append(
        sparkle
    )


# ============================================================
# SCATTER FLOWERS
# ============================================================

def scatter_flowers(
    x,
    y
):

    for flower in particles:

        # ----------------------------------------------------
        # DISTANCE FROM HAND
        # ----------------------------------------------------

        dx = flower.x - x

        dy = flower.y - y


        distance = math.sqrt(

            dx * dx
            +
            dy * dy

        )


        if distance < 5:

            distance = 5


        # ----------------------------------------------------
        # OUTWARD DIRECTION
        # ----------------------------------------------------

        direction_x = (
            dx / distance
        )

        direction_y = (
            dy / distance
        )


        # ----------------------------------------------------
        # FAST NATURAL SCATTER
        # ----------------------------------------------------

        influence = max(

            0.45,

            1.0
            -
            (
                distance
                /
                900.0
            )

        )


        speed = random.uniform(

            7.0,
            13.0

        ) * influence


        # ----------------------------------------------------
        # RANDOM SIDE MOVEMENT
        # ----------------------------------------------------

        side_x = random.uniform(
            -2.0,
            2.0
        )

        side_y = random.uniform(
            -2.0,
            2.0
        )


        # ----------------------------------------------------
        # OUTWARD VELOCITY
        # ----------------------------------------------------

        flower.vx = (

            direction_x * speed
            +
            side_x

        )

        flower.vy = (

            direction_y * speed
            +
            side_y

        )


        # ====================================================
        # SWIRL
        # ====================================================

        swirl_x = -direction_y

        swirl_y = direction_x


        swirl_strength = random.uniform(

            1.0,
            2.8

        )


        flower.vx += (

            swirl_x
            *
            swirl_strength

        )


        flower.vy += (

            swirl_y
            *
            swirl_strength

        )


        # ----------------------------------------------------
        # ENABLE SCATTER
        # ----------------------------------------------------

        flower.scattering = True


        # ----------------------------------------------------
        # FADE
        # ----------------------------------------------------

        flower.fade_speed = random.uniform(

            0.005,
            0.010

        )


        # ----------------------------------------------------
        # FLOWER ROTATION
        # ----------------------------------------------------

        flower.rotation_speed = random.uniform(

            -0.8,
            0.8

        )


    # ========================================================
    # MAGICAL SPARKLE BURST
    # ========================================================

    for _ in range(12):

        # Mostly white with some gold

        sparkle = Sparkle(

            x + random.uniform(
                -25,
                25
            ),

            y + random.uniform(
                -25,
                25
            ),

            golden=(
                random.random() < 0.35
            )

        )


        sparkle.vx *= 1.8

        sparkle.vy *= 1.8


        sparkle.size = random.uniform(
            1.0,
            2.5
        )


        sparkles.append(
            sparkle
        )


    # ========================================================
    # PLAY SCATTER SOUND
    # ========================================================

    if scatter_sound is not None:

        scatter_channel.stop()

        scatter_channel.play(
            scatter_sound
        )


# ============================================================
# ROTATE IMAGE
# ============================================================

def rotate_image(
    image,
    angle
):

    h, w = image.shape[:2]

    center = (

        w // 2,
        h // 2

    )


    matrix = cv2.getRotationMatrix2D(

        center,

        angle,

        1.0

    )


    return cv2.warpAffine(

        image,

        matrix,

        (w, h),

        flags=cv2.INTER_LINEAR,

        borderMode=cv2.BORDER_CONSTANT,

        borderValue=(
            0,
            0,
            0,
            0
        )

    )


# ============================================================
# DRAW FLOWER
# ============================================================

def draw_flower(
    frame,
    flower
):

    image = flower.image


    h, w = image.shape[:2]


    # --------------------------------------------------------
    # SCALE
    # --------------------------------------------------------

    scale = (

        flower.size
        /
        max(
            h,
            w
        )

    )


    new_w = max(

        1,

        int(
            w * scale
        )

    )


    new_h = max(

        1,

        int(
            h * scale
        )

    )


    image = cv2.resize(

        image,

        (
            new_w,
            new_h
        ),

        interpolation=cv2.INTER_AREA

    )


    # --------------------------------------------------------
    # ROTATE
    # --------------------------------------------------------

    image = rotate_image(

        image,

        flower.angle

    )


    new_h, new_w = (
        image.shape[:2]
    )


    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    x = int(

        flower.x
        -
        new_w / 2

    )


    y = int(

        flower.y
        -
        new_h / 2

    )


    # --------------------------------------------------------
    # OFF-SCREEN CHECK
    # --------------------------------------------------------

    if (

        x >= frame.shape[1]

        or

        y >= frame.shape[0]

        or

        x + new_w <= 0

        or

        y + new_h <= 0

    ):

        return


    x1 = max(
        0,
        x
    )

    y1 = max(
        0,
        y
    )


    x2 = min(

        frame.shape[1],

        x + new_w

    )


    y2 = min(

        frame.shape[0],

        y + new_h

    )


    fx1 = x1 - x

    fy1 = y1 - y


    fx2 = fx1 + (
        x2 - x1
    )

    fy2 = fy1 + (
        y2 - y1
    )


    crop = image[

        fy1:fy2,

        fx1:fx2

    ]


    if crop.size == 0:

        return


    # ========================================================
    # PNG WITH TRANSPARENCY
    # ========================================================

    if crop.shape[2] == 4:

        alpha = (

            crop[:, :, 3]
            .astype(float)
            /
            255.0

        )


        alpha *= flower.life


        for c in range(3):

            frame[

                y1:y2,

                x1:x2,

                c

            ] = (

                alpha
                *
                crop[
                    :,
                    :,
                    c
                ]

                +

                (
                    1 - alpha
                )
                *
                frame[
                    y1:y2,
                    x1:x2,
                    c
                ]

            )


    # ========================================================
    # NORMAL JPG
    # ========================================================

    else:

        if flower.life < 1:

            alpha = flower.life


            for c in range(3):

                frame[

                    y1:y2,

                    x1:x2,

                    c

                ] = (

                    alpha
                    *
                    crop[
                        :,
                        :,
                        c
                    ]

                    +

                    (
                        1 - alpha
                    )
                    *
                    frame[
                        y1:y2,
                        x1:x2,
                        c
                    ]

                )


        else:

            frame[

                y1:y2,

                x1:x2

            ] = crop


# ============================================================
# DRAW SPARKLE
# ============================================================

def draw_sparkle(
    frame,
    sparkle
):

    if sparkle.life <= 0:

        return


    x = int(
        sparkle.x
    )

    y = int(
        sparkle.y
    )


    # --------------------------------------------------------
    # CAMERA BOUNDARY
    # --------------------------------------------------------

    if (

        x < 0

        or

        y < 0

        or

        x >= frame.shape[1]

        or

        y >= frame.shape[0]

    ):

        return


    # --------------------------------------------------------
    # FADE
    # --------------------------------------------------------

    alpha = max(

        0.0,

        min(
            1.0,
            sparkle.life
        )

    )


    brightness = int(

        255 * alpha

    )


    radius = max(

        1,

        int(
            sparkle.size
        )

    )


    # --------------------------------------------------------
    # GOLDEN SPARKLE
    # --------------------------------------------------------

    if sparkle.golden:

        # BGR format:
        # warm golden yellow

        b = int(
            40 * alpha
        )

        g = int(
            190 * alpha
        )

        r = int(
            255 * alpha
        )


        cv2.circle(

            frame,

            (x, y),

            radius,

            (
                b,
                g,
                r
            ),

            -1

        )


    # --------------------------------------------------------
    # WHITE SPARKLE
    # --------------------------------------------------------

    else:

        cv2.circle(

            frame,

            (x, y),

            radius,

            (
                brightness,
                brightness,
                brightness
            ),

            -1

        )


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(
    0
)


cap.set(

    cv2.CAP_PROP_FRAME_WIDTH,

    960

)


cap.set(

    cv2.CAP_PROP_FRAME_HEIGHT,

    720

)


if not cap.isOpened():

    print(
        "ERROR: Camera could not be opened."
    )

    pygame.quit()

    exit()


# ============================================================
# TWO HAND SMOOTHING
# ============================================================

smooth_positions = [

    [None, None],

    [None, None]

]


SMOOTHING = 0.32


def smooth_position(

    hand_id,

    x,

    y

):

    old_x = (

        smooth_positions[
            hand_id
        ][0]

    )


    old_y = (

        smooth_positions[
            hand_id
        ][1]

    )


    if old_x is None:

        smooth_positions[
            hand_id
        ][0] = x

        smooth_positions[
            hand_id
        ][1] = y


    else:

        smooth_positions[
            hand_id
        ][0] += (

            x
            -
            old_x

        ) * SMOOTHING


        smooth_positions[
            hand_id
        ][1] += (

            y
            -
            old_y

        ) * SMOOTHING


    return (

        int(

            smooth_positions[
                hand_id
            ][0]

        ),

        int(

            smooth_positions[
                hand_id
            ][1]

        )

    )


# ============================================================
# DISTANCE
# ============================================================

def distance(
    a,
    b
):

    dx = a.x - b.x

    dy = a.y - b.y

    return math.sqrt(

        dx * dx
        +
        dy * dy

    )


# ============================================================
# FINGER EXTENDED
# ============================================================

def finger_is_extended(

    hand,

    tip_id,

    pip_id

):

    wrist = hand[0]

    tip = hand[
        tip_id
    ]

    pip = hand[
        pip_id
    ]


    tip_distance = distance(

        wrist,

        tip

    )


    pip_distance = distance(

        wrist,

        pip

    )


    return (

        tip_distance
        >
        pip_distance
        *
        1.20

    )


# ============================================================
# OPEN HAND
# ============================================================

def is_open_hand(
    hand
):

    index = finger_is_extended(

        hand,
        8,
        6

    )


    middle = finger_is_extended(

        hand,
        12,
        10

    )


    ring = finger_is_extended(

        hand,
        16,
        14

    )


    pinky = finger_is_extended(

        hand,
        20,
        18

    )


    return (

        index

        and

        middle

        and

        ring

        and

        pinky

    )


# ============================================================
# TIMING
# ============================================================

last_spawn = [

    0,
    0

]


# IMPORTANT:
# No timer controls scattering.
#
# This variable only prevents the SAME open-hand gesture
# from repeatedly triggering the sound/scatter every frame.

previous_open_hand = [

    False,
    False

]


timestamp = 0


# ============================================================
# MAIN LOOP
# ============================================================

with HandLandmarker.create_from_options(

    options

) as landmarker:

    while True:

        success, frame = cap.read()


        if not success:

            break


        # ----------------------------------------------------
        # MIRROR CAMERA
        # ----------------------------------------------------

        frame = cv2.flip(

            frame,

            1

        )


        height, width = (

            frame.shape[:2]

        )


        # ----------------------------------------------------
        # RGB
        # ----------------------------------------------------

        rgb = cv2.cvtColor(

            frame,

            cv2.COLOR_BGR2RGB

        )


        mp_image = mp.Image(

            image_format=
            mp.ImageFormat.SRGB,

            data=rgb

        )


        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        timestamp = int(

            time.monotonic()
            *
            1000

        )


        # ----------------------------------------------------
        # HAND DETECTION
        # ----------------------------------------------------

        result = (

            landmarker.detect_for_video(

                mp_image,

                timestamp

            )

        )


        # Track which slots were seen

        current_hand_slots = set()


        # ====================================================
        # PROCESS BOTH HANDS
        # ====================================================

        if result.hand_landmarks:

            for (

                hand_id,
                hand

            ) in enumerate(

                result.hand_landmarks

            ):

                if hand_id >= 2:

                    continue


                current_hand_slots.add(
                    hand_id
                )


                # ------------------------------------------------
                # INDEX FINGER
                # ------------------------------------------------

                index_tip = hand[8]


                raw_x = int(

                    index_tip.x
                    *
                    width

                )


                raw_y = int(

                    index_tip.y
                    *
                    height

                )


                # ------------------------------------------------
                # SMOOTH
                # ------------------------------------------------

                x, y = smooth_position(

                    hand_id,

                    raw_x,

                    raw_y

                )


                # ------------------------------------------------
                # OPEN HAND
                # ------------------------------------------------

                open_hand = (

                    is_open_hand(

                        hand

                    )

                )


                current_time = (

                    time.time()

                )


                # =================================================
                # FLOWER FORMATION
                # =================================================

                if not open_hand:

                    if (

                        current_time
                        -
                        last_spawn[
                            hand_id
                        ]

                        >

                        0.035

                    ):

                        add_flower(

                            x,

                            y

                        )


                        add_sparkles(

                            x,

                            y

                        )


                        last_spawn[
                            hand_id
                        ] = (

                            current_time

                        )


                    # ------------------------------------------------
                    # START FORMATION SOUND
                    # ------------------------------------------------

                    if (

                        formation_sound is not None

                        and

                        not formation_playing

                    ):

                        formation_channel.play(

                            formation_sound

                        )

                        formation_playing = True


                # =================================================
                # OPEN HAND / SCATTER
                # =================================================

                if open_hand:

                    # Stop formation sound

                    if formation_playing:

                        formation_channel.fadeout(
                            250
                        )

                        formation_playing = False


                    # ------------------------------------------------
                    # SCATTER ONLY WHEN HAND CHANGES
                    # FROM CLOSED/FORMING TO OPEN
                    # ------------------------------------------------

                    if not previous_open_hand[
                        hand_id
                    ]:

                        scatter_flowers(

                            x,

                            y

                        )


                else:

                    previous_open_hand[
                        hand_id
                    ] = False


                # Remember current state

                previous_open_hand[
                    hand_id
                ] = open_hand


        # ====================================================
        # UPDATE FLOWERS
        # ====================================================

        alive = []


        for flower in particles:

            if flower.scattering:

                # ------------------------------------------------
                # MOVE
                # ------------------------------------------------

                flower.x += (

                    flower.vx

                )


                flower.y += (

                    flower.vy

                )


                # ------------------------------------------------
                # GRAVITY
                # ------------------------------------------------

                flower.vy += 0.10


                # ------------------------------------------------
                # AIR RESISTANCE
                # ------------------------------------------------

                flower.vx *= 0.985

                flower.vy *= 0.985


                # ------------------------------------------------
                # ROTATION
                # ------------------------------------------------

                flower.angle += (

                    flower.rotation_speed

                )


            else:

                # ------------------------------------------------
                # NORMAL FLOATING
                # ------------------------------------------------

                flower.float_phase += (

                    0.04
                    *
                    flower.float_speed

                )


                flower.x += (

                    flower.vx

                    +

                    math.sin(

                        flower.float_phase

                    )
                    *
                    flower.float_amount

                )


                flower.y += (

                    flower.vy

                    +

                    math.cos(

                        flower.float_phase

                    )
                    *
                    flower.float_amount

                )


                flower.angle += (

                    flower.rotation_speed

                )


            # ------------------------------------------------
            # FADE
            # ------------------------------------------------

            flower.life -= (

                flower.fade_speed

            )


            if flower.life > 0:

                alive.append(
                    flower
                )


        particles = alive


        # ====================================================
        # UPDATE SPARKLES
        # ====================================================

        alive_sparkles = []


        for sparkle in sparkles:

            sparkle.x += (

                sparkle.vx

            )


            sparkle.y += (

                sparkle.vy

            )


            sparkle.vx *= 0.98

            sparkle.vy *= 0.98


            sparkle.life -= (

                sparkle.fade_speed

            )


            if sparkle.life > 0:

                alive_sparkles.append(

                    sparkle

                )


        sparkles = alive_sparkles


        # ====================================================
        # DRAW FLOWERS
        # ====================================================

        for flower in particles:

            draw_flower(

                frame,

                flower

            )


        # ====================================================
        # DRAW SPARKLES
        # ====================================================

        for sparkle in sparkles:

            draw_sparkle(

                frame,

                sparkle

            )


        # ====================================================
        # LIMIT PARTICLES
        # ====================================================

        if len(particles) > 180:

            particles = (

                particles[-180:]

            )


        if len(sparkles) > 60:

            sparkles = (

                sparkles[-60:]

            )


        # ====================================================
        # SHOW CAMERA
        # ====================================================

        cv2.imshow(

            "FlowerFlow",

            frame

        )


        # ====================================================
        # QUIT
        # ====================================================

        key = (

            cv2.waitKey(1)
            &
            0xFF

        )


        if key == ord("q"):

            break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

pygame.quit()