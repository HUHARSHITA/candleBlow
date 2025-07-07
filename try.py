import pygame
import cv2
import sys
import mediapipe as mp
import random
import time

# Init
pygame.init()
cam = cv2.VideoCapture(0)

# MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# Screen
WIDTH, HEIGHT = 1000, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magic Candle 🎂")
clock = pygame.time.Clock()

# Load and scale cake frames
cake_original_size = (1440, 1024)
cake_target_size = (600, 500)
cake_frames = [pygame.transform.scale(pygame.image.load(f"assets/cake_on{i}.png"), cake_target_size) for i in range(1, 4)]
cake_off_frame = [pygame.transform.scale(pygame.image.load(f"assets/cake_off{i}.png"), cake_target_size) for i in range(1, 3)]

# Confetti
confetti_imgs = [pygame.image.load(f"assets/confetti_{i}.png").convert_alpha() for i in range(1, 3)]
confetti_particles = []

# Music
pygame.mixer.init()
blow_sound = pygame.mixer.Sound("assets/happyBirthday.mp3")

# Blow detection variables
blow_count = 0
blown = False
cheek_history = []
max_cheek = 0
mouth_open = 0
frame_idx = 0
music_playing = False
reset_timer = None  # Track time after blow

# Generate confetti
def reset_confetti():
    confetti_particles.clear()
    for _ in range(25):
        x = random.randint(0, WIDTH)
        y = random.randint(-300, -50)
        img = random.choice(confetti_imgs)
        speed = random.uniform(2.0, 3.5)
        confetti_particles.append({
            "x": x,
            "y": y,
            "img": pygame.transform.scale(img, (250, 200)),
            "speed": speed
        })

# Reset everything
def full_reset():
    global blow_count, blown, max_cheek, cheek_history, confetti_particles, frame_idx, music_playing, reset_timer
    blow_count = 0
    blown = False
    max_cheek = 0
    cheek_history.clear()
    confetti_particles.clear()
    frame_idx = 0
    music_playing = False
    reset_timer = None
    print("🔄 Auto reset complete")

# Main loop
running = True
while running:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Webcam input
    ret, frame = cam.read()
    if ret:
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = face_mesh.process(rgb)
        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark
            h, w, _ = frame.shape

            def px(id): return int(lm[id].x * w), int(lm[id].y * h)

            top_lip = px(13)
            bottom_lip = px(14)
            left_cheek = px(234)
            right_cheek = px(454)

            mouth_open = abs(top_lip[1] - bottom_lip[1])
            cheek_width = abs(right_cheek[0] - left_cheek[0])
            cheek_history.append(cheek_width)
            if len(cheek_history) > 10:
                cheek_history.pop(0)

            if cheek_width > max_cheek:
                max_cheek = cheek_width

            if not blown and mouth_open > 10 and (max_cheek - cheek_width) > 2:
                blow_count += 1
                blown = True
                print(f"💨 Blow #{blow_count}")
                if blow_count == 1:
                    reset_confetti()
                    blow_sound.play()
                    music_playing = True
                    reset_timer = time.time()  # Start countdown for auto-reset

        # Show webcam on right
        cam_resized = cv2.resize(rgb, (400, 500))
        cam_surface = pygame.surfarray.make_surface(cam_resized.swapaxes(0, 1))
        screen.blit(cam_surface, (600, 0))

    # Cake on left
    if blow_count == 0:
        frame_idx = (frame_idx + 1) % (len(cake_frames) * 10)
        cake_img = cake_frames[frame_idx // 10]
    else:
        frame_idx = (frame_idx + 1) % (len(cake_off_frame) * 10)
        cake_img = cake_off_frame[frame_idx // 10]

    screen.blit(cake_img, (0, 0))

    # Confetti
    for p in confetti_particles:
        screen.blit(p["img"], (p["x"], p["y"]))
        p["y"] += p["speed"]
        if p["y"] > HEIGHT:
            p["y"] = random.randint(-300, -50)
            p["x"] = random.randint(0, WIDTH)
            p["speed"] = random.uniform(1.5, 4)

    # Auto reset after 10 sec
    if blown and reset_timer:
        if time.time() - reset_timer > 10:
            blow_sound.stop()
            full_reset()

    pygame.display.update()
    clock.tick(30)

# Cleanup
cam.release()
pygame.quit()
sys.exit()
