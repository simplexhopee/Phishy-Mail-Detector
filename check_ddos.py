import os
import sys
from datetime import datetime, timedelta

# Arguments
sender_email = sys.argv[1]
email_path = sys.argv[2]
mailbox = sys.argv[3]

# Configuration
threshold = 8  # Number of emails to trigger DDOS protection
time_frame = timedelta(minutes=1)  # Time frame to check for DDOS (1 minute)

# Path to the directory containing emails
basepath_inbox = f"C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\{mailbox}\Inbox"
basepath_phishy = f"C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\{mailbox}\Junk E-mail"

def get_inbox_files():
    """Get all email files in the inbox directory."""
    return [os.path.join(basepath_inbox, f) for f in os.listdir(basepath_inbox) if os.path.isfile(os.path.join(basepath_inbox, f))]

def get_phishy_files():
    """Get all email files in the phishy directory."""
    return [os.path.join(basepath_phishy, f) for f in os.listdir(basepath_phishy) if os.path.isfile(os.path.join(basepath_phishy, f))]

def get_email_sender(email_file):
    """Extract the sender from the email file."""
    with open(email_file, 'r') as f:
        for line in f:
            if line.startswith("From:"):
                return line.split(":", 1)[1].strip()
    return None

def get_email_datetime(email_file):
    """Extract the datetime from the email file."""
    return datetime.fromtimestamp(os.path.getmtime(email_file))

def check_ddos(sender_email):
    """Check for DDOS attack by counting recent emails from the same sender."""
    email_files = get_inbox_files()
    phishy_files = get_phishy_files()
    current_time = datetime.now()
    count = 0
    delete_any = False
    for email_file in email_files:
        if get_email_sender(email_file) == sender_email:
            email_time = get_email_datetime(email_file)
            if current_time - email_time <= time_frame:
                count += 1
                if count >= threshold:
                    # Delete the emails from inbox
                    if delete_any == False : delete_any = True
                    for email_file in email_files:
                        if get_email_sender(email_file) == sender_email:
                            os.remove(email_file)
                    print("DDOS attack detected. Emails deleted.")
                    
    print("No DDOS attack detected for inbox.")
    for email_file in phishy_files:
        if get_email_sender(email_file) == sender_email:
            email_time = get_email_datetime(email_file)
            if current_time - email_time <= time_frame:
                count += 1
                if count >= threshold:
                    if delete_any == False : delete_any = True
                    # Delete the emails from phishy folder
                    for email_file in phishy_files:
                        if get_email_sender(email_file) == sender_email:
                            os.remove(email_file)
                    print("DDOS attack detected. Emails deleted.")
                    
    print("No DDOS attack detected for phishy.")
    if delete_any == True: os.remove(email_path)



if __name__ == "__main__":
    check_ddos(sender_email)
