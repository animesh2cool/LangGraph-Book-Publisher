class HumanReviewAgent:
    def __init__(self):
        pass

    def review(self, reviewed_text: str) -> dict:
        print("\n --- HUMAN REVIEW REQUIRED ---\n")
        print("Suggested Final Text:\n")
        print(reviewed_text)
        print("\nYou can now edit this text. Press ENTER to keep it as-is.")

        edited_text = input("Paste revised content here (or press ENTER to accept): ").strip()
        final_text = edited_text if edited_text else reviewed_text

        return {"final_text": final_text}