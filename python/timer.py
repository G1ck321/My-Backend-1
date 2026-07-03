import time

def countdown_timer(seconds):
    while seconds > 0:
        # divmod(x, y) returns a tuple (x//y, x%y)
        mins, secs = divmod(seconds, 60)
        
        # Format the time as MM:SS with leading zeros
        timer_display = f"{mins:02d}:{secs:02d}"
        
        # \r moves the cursor to the start of the line to overwrite it
        print(f"Time remaining: {timer_display}", end="\r")
        
        time.sleep(1) #Wait for one second
        seconds -= 1

    print("\nTime's up!")

# Example: 10-second timer
countdown_timer(10)
