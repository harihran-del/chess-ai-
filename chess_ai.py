import time
import chess
import chess.engine
import cv2
import numpy as np
import mss
from tkinter import Tk, Label, StringVar

# Stockfish path
stockfish_path = r"C:\Users\harih\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"

# Initialize Stockfish engine
engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

# Initialize screen capture
sct = mss.mss()

# Define the region of the screen where the chessboard is located
# Adjust these values based on your screen resolution and chessboard position
chessboard_region = {
    "top": 200,    # Distance from the top of the screen
    "left": 500,   # Distance from the left of the screen
    "width": 800,  # Width of the chessboard region
    "height": 800  # Height of the chessboard region
}

# Chessboard detection parameters
board_size = 800  # Size of the chessboard in pixels
square_size = board_size // 8

# Function to capture the chessboard region
def capture_chessboard_region():
    screenshot = sct.grab(chessboard_region)
    img = np.array(screenshot)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

# Function to detect the chessboard
def detect_chessboard(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (7, 7), None)  # 7x7 inner corners for 8x8 board
    
    if ret:
        # Draw the corners for visualization
        debug_image = image.copy()
        cv2.drawChessboardCorners(debug_image, (7, 7), corners, ret)
        cv2.imshow("Detected Corners", debug_image)
        cv2.waitKey(500)  # Show for 500ms
        
        # Refine the corners for better accuracy
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        # Warp perspective to get a top-down view of the chessboard
        src_points = np.float32([corners[0][0], corners[6][0], corners[42][0], corners[48][0]])
        dst_points = np.float32([[0, 0], [board_size, 0], [0, board_size], [board_size, board_size]])
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        warped = cv2.warpPerspective(image, matrix, (board_size, board_size))
        
        return warped
    else:
        print("Chessboard not detected")
        return None

# Function to get the current board state
def get_board_state(warped_image):
    board = chess.Board()
    for i in range(8):
        for j in range(8):
            x1, y1 = j * square_size, i * square_size
            x2, y2 = (j + 1) * square_size, (i + 1) * square_size
            square = warped_image[y1:y2, x1:x2]
            
            # Detect pieces using color thresholding (simplified for demonstration)
            # You can improve this with a trained ML model for piece recognition
            if np.mean(square) > 127:  # Light square
                pass
            else:  # Dark square
                pass
    
    return board.fen()

# Function to update the floating box
def update_floating_box(root, move_var, best_move_var):
    move_var.set(f"Your Move: {your_move}\nOpponent's Move: {opponent_move}\nBest Move: {best_move}")
    root.update()

# Initialize the floating box
root = Tk()
root.title("Chess AI Assistant")
root.geometry("300x100+10+10")  # Position the box at the top-left corner
root.attributes("-topmost", True)  # Keep the box on top of other windows

move_var = StringVar()
best_move_var = StringVar()

label = Label(root, textvariable=move_var, font=("Arial", 14))
label.pack()

# Main loop
your_move = ""
opponent_move = ""
last_fen = None

try:
    while True:
        # Capture the chessboard region
        image = capture_chessboard_region()
        warped = detect_chessboard(image)
        
        if warped is not None:
            # Get the current board state
            fen = get_board_state(warped)
            
            if fen != last_fen:  # Check if the board state has changed
                print(f"Current FEN: {fen}")
                
                # Get the best move from Stockfish
                board = chess.Board(fen)
                result = engine.play(board, chess.engine.Limit(time=2.0))
                best_move = result.move
                
                # Update the floating box
                update_floating_box(root, move_var, best_move_var)
                
                last_fen = fen
        
        time.sleep(2)  # Wait 2 seconds before checking again

except KeyboardInterrupt:
    print("Exiting...")

finally:
    engine.quit()
    root.destroy()