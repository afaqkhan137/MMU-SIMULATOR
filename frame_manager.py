class FrameManager:


    def __init__(self, num_frames):

        self.num_frames = num_frames
        # List of free frame numbers
        self.free_frames = list(range(num_frames))
        # Set of used frame numbers
        self.used_frames = set()

    def has_free_frames(self):

        return len(self.free_frames) > 0

    def get_free_count(self):

        return len(self.free_frames)

    def get_used_count(self):

        return len(self.used_frames)

    def allocate_frame(self):

        if not self.free_frames:
            raise Exception("No free frames available! Need eviction.")

        # Take the first free frame
        frame = self.free_frames.pop(0)
        self.used_frames.add(frame)
        return frame

    def free_frame(self, frame):

        if frame in self.used_frames:
            self.used_frames.remove(frame)
            self.free_frames.append(frame)
            return True
        return False

    def is_frame_free(self, frame):

        return frame in self.free_frames

    def is_frame_used(self, frame):

        return frame in self.used_frames

    def print_status(self):

        print(f"\n--- Frame Manager Status ---")
        print(f"Total frames:   {self.num_frames}")
        print(f"Free frames:    {self.get_free_count()} {self.free_frames}")
        print(f"Used frames:    {self.get_used_count()} {sorted(self.used_frames)}")
        print(f"----------------------------")


# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING FRAME MANAGER")
    print("=" * 50)

    # Create frame manager with 16 frames (for 64KB RAM with 4KB pages)
    fm = FrameManager(16)

    print("\n--- Initial State ---")
    fm.print_status()

    print("\n--- Allocating 5 frames ---")
    for i in range(5):
        frame = fm.allocate_frame()
        print(f"Allocated frame: {frame}")

    fm.print_status()

    print("\n--- Freeing frame 2 ---")
    fm.free_frame(2)
    fm.print_status()

    print("\n--- Allocating another frame ---")
    frame = fm.allocate_frame()
    print(f"Allocated frame: {frame}")
    fm.print_status()

    print("\nChecking specific frames\n")
    print(f"Is frame 0 free? {fm.is_frame_free(0)}")
    print(f"Is frame 0 used? {fm.is_frame_used(0)}")
    print(f"Is frame 2 free? {fm.is_frame_free(2)}")
    print(f"Is frame 15 free? {fm.is_frame_free(15)}")

    print("\n--- Has free frames? ---")
    print(f"Free frames available: {fm.has_free_frames()}")
    print(f"Free count: {fm.get_free_count()}")
    print(f"Used count: {fm.get_used_count()}")

    print("\n" + "=" * 50)
    print("✅ Frame Manager works!")
