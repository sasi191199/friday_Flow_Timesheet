import os
import smtplib
from pathlib import Path
from datetime import datetime, timedelta
from email.message import EmailMessage

from PIL import Image
from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent

INPUT_FOLDER = BASE_DIR / "input_images"
BACKUP_FOLDER = BASE_DIR / "backup_images"
OUTPUT_FOLDER = BASE_DIR / "output_pdfs"

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

PERSON_NAME = "Bonthu_Sasivardhan"


def get_images_from_input_folder():
    images = []

    for file in INPUT_FOLDER.iterdir():
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(file)

    images.sort(key=lambda file: file.stat().st_mtime)
    return images


def get_current_week_monday():
    today = datetime.now().date()
    return today - timedelta(days=today.weekday())


def format_date(date_value):
    return date_value.strftime("%m_%d_%Y")


def rename_images_by_week(images):
    renamed_images = []

    current_week_monday = get_current_week_monday()
    total_images = len(images)

    for index, image in enumerate(images):
        weeks_back = total_images - index - 1

        week_start = current_week_monday - timedelta(weeks=weeks_back)
        week_end = week_start + timedelta(days=6)

        start_text = format_date(week_start)
        end_text = format_date(week_end)

        new_name = f"{PERSON_NAME}_{start_text}_{end_text}{image.suffix.lower()}"
        new_path = INPUT_FOLDER / new_name

        image.rename(new_path)
        renamed_images.append(new_path)

        print(f"Renamed: {image.name} -> {new_name}")

    return renamed_images


def convert_images_to_pdfs(images):
    pdf_files = []

    for image_path in images:
        pdf_name = image_path.stem + ".pdf"
        pdf_path = OUTPUT_FOLDER / pdf_name

        image = Image.open(image_path).convert("RGB")
        image.save(pdf_path)

        pdf_files.append(pdf_path)

        print(f"PDF created: {pdf_path.name}")

    return pdf_files


def send_email_with_pdfs(pdf_files):
    load_dotenv()

    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("APP_PASSWORD")

    receivers = [
        {
            "email": os.getenv("RECEIVER_1_EMAIL"),
            "name": os.getenv("RECEIVER_1_NAME")
        },
        {
            "email": os.getenv("RECEIVER_2_EMAIL"),
            "name": os.getenv("RECEIVER_2_NAME")
        }
    ]

    if not sender_email or not app_password:
        raise ValueError("SENDER_EMAIL or APP_PASSWORD is missing in .env file.")

    for receiver in receivers:
        receiver_email = receiver["email"]
        receiver_name = receiver["name"]

        if not receiver_email or not receiver_name:
            continue

        msg = EmailMessage()
        msg["Subject"] = "Weekly Timesheet Submission"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        msg.set_content(f"""
Hi {receiver_name},

Please find attached the weekly timesheet(s) for your review.

Each file is named according to the corresponding week range.

Let me know if any corrections or additional details are needed.

Thanks & Regards,
Bonthu Sasivardhan
""")

        for pdf_file in pdf_files:
            with open(pdf_file, "rb") as file:
                msg.add_attachment(
                    file.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=pdf_file.name
                )

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        print(f"Email sent successfully to {receiver_name} - {receiver_email}")


def move_images_to_backup(images):
    for image_path in images:
        backup_path = BACKUP_FOLDER / image_path.name
        image_path.rename(backup_path)
        print(f"Moved to backup: {image_path.name}")


def main():
    print("Weekly Image Emailer started...")

    images = get_images_from_input_folder()
    print(f"Images found: {len(images)}")

    if len(images) == 0:
        print("No images found in input_images folder. Stopping process.")
        return

    renamed_images = rename_images_by_week(images)

    pdf_files = convert_images_to_pdfs(renamed_images)

    send_email_with_pdfs(pdf_files)

    move_images_to_backup(renamed_images)

    print("Process completed successfully.")


if __name__ == "__main__":
    main()