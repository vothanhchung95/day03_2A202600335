# src/tools/tools.py

def search_dictionary(word: str) -> str:
    """
    Tra cứu nghĩa của một từ tiếng Anh và cách sử dụng.
    """
    mock_db = {
        "diligent": "Nghĩa: Siêng năng, cần cù. Ví dụ: He is a diligent student.",
        "feeling blue": "Nghĩa: Cảm thấy buồn bã.",
    }
    return mock_db.get(word.lower(), f"Không tìm thấy nghĩa của từ '{word}'.")

def save_to_flashcard(word: str, definition: str) -> str:
    """
    Lưu từ vựng và định nghĩa vào bộ thẻ nhớ (Flashcard).
    """
    print(f"--- LOG: Đã lưu {word} ---")
    return f"Thành công: Đã thêm '{word}' vào bộ thẻ nhớ."

# SỬA LẠI BIẾN TOOLS TẠI ĐÂY
# Thay vì chỉ truyền hàm, ta truyền một dictionary chứa thông tin hàm
tools = [
    {
        "name": "search_dictionary",
        "description": "Tra cứu nghĩa của một từ tiếng Anh và cách sử dụng.",
        "func": search_dictionary  # Giữ lại tham chiếu đến hàm để gọi sau này
    },
    {
        "name": "save_to_flashcard",
        "description": "Lưu từ vựng và định nghĩa vào bộ thẻ nhớ (Flashcard).",
        "func": save_to_flashcard
    }
]