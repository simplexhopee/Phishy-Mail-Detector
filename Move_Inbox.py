import os
import shutil
import xml.etree.ElementTree as ET
import sys

def move_mail_files(junk_folder, inbox_folder, mail_ids):
    junk_index = os.path.join(junk_folder, '_index.xml')
    inbox_index = os.path.join(inbox_folder, '_index.xml')

    # Ensure the Inbox folder exists
    if not os.path.exists(inbox_folder):
        os.makedirs(inbox_folder)

    # Parse the XML files
    junk_tree = ET.parse(junk_index)
    junk_root = junk_tree.getroot()
    inbox_tree = ET.parse(inbox_index)
    inbox_root = inbox_tree.getroot()

    for mail_id in mail_ids:
        mail_file = os.path.join(junk_folder, f"{mail_id}")

        # Move the mail file to the Inbox folder
        shutil.move(mail_file, inbox_folder)

        # Remove the specified header from the mail file
        new_mail_file = os.path.join(inbox_folder, f"{mail_id}")
        with open(new_mail_file, 'r') as file:
            lines = file.readlines()
        with open(new_mail_file, 'w') as file:
            for line in lines:
                if 'X-ME-Content: Deliver-To=Junk' not in line:
                    file.write(line)

        # Find and move the corresponding XML node
        for element in junk_root.findall('ELEMENT'):
            if element.get('ID') == mail_id:
                inbox_root.append(element)
                junk_root.remove(element)
                break

    # Write the updated XML files back
    junk_tree.write(junk_index)
    inbox_tree.write(inbox_index)

if __name__ == "__main__":
    junk_folder = sys.argv[1]
    inbox_folder = sys.argv[2]
    mail_ids = sys.argv[3].split(',')

    move_mail_files(junk_folder, inbox_folder, mail_ids)
