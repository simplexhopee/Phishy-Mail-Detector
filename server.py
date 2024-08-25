from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import shutil
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser
import re
import quopri
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key="api-key-here",
)


app = Flask(__name__)
CORS(app)  # Enable CORS



def move_mail_files(junk_folder, inbox_folder, mail_ids):
    junk_index = os.path.join(junk_folder, '_index.xml')
    inbox_index = os.path.join(inbox_folder, '_index.xml')
    print(mail_ids)

    # Ensure the Inbox folder exists
    if not os.path.exists(inbox_folder):
        os.makedirs(inbox_folder)

    # Parse the XML files
    junk_tree = ET.parse(junk_index)
    junk_root = junk_tree.getroot()
    inbox_tree = ET.parse(inbox_index)
    inbox_root = inbox_tree.getroot()

    # Find the highest UID in the inbox folder
    highest_inbox_uid = 0
    for element in inbox_root.findall('ELEMENT'):
        try:
            uid = int(element.get('UID'))
            if uid > highest_inbox_uid:
                highest_inbox_uid = uid
        except ValueError as e:
            print(f"Skipping invalid UID in inbox: {element.get('UID')}")

    # Function to update LASTUID attribute
    def update_last_uid(root):
        elements = root.findall('ELEMENT')
        valid_uids = [int(element.get('UID')) for element in elements if element.get('UID').isdigit()]
        if valid_uids:
            last_uid = max(valid_uids)
            root.set('LASTUID', f"x{last_uid:08}")
        else:
            root.set('LASTUID', "x00000000")

    for mail_id in mail_ids:
        mail_file = os.path.join(junk_folder, f"{mail_id}")
        print(mail_file)

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
                highest_inbox_uid += 1
                element.set('UID', str(highest_inbox_uid))
                inbox_root.append(element)
                junk_root.remove(element)
                break

    # Update the LASTUID attribute
    update_last_uid(junk_root)
    update_last_uid(inbox_root)

    # Write the updated XML files back
    def write_xml(tree, file_path):
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        with open(file_path, 'r') as file:
            lines = file.readlines()
        with open(file_path, 'w') as file:
            for line in lines:
                if line.strip().startswith('<BASEELEMENT LASTUID="') and line.strip().endswith('" />'):
                    uid_value = line.strip().split('"')[1]
                    file.write(f'<BASEELEMENT LASTUID="{uid_value}"></BASEELEMENT>\n')
                else:
                    file.write(line)

    write_xml(junk_tree, junk_index)
    write_xml(inbox_tree, inbox_index)



@app.route('/move-mails', methods=['POST'])
def move_mails():
    try:
        data = request.json
        print("Received payload:", data)  # Debugging information

        junk_folder = r'C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\{}\Junk E-mail'.format(data['mailbox'])

        inbox_folder = r'C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\{}\Inbox'.format(data['mailbox'])

        mail_ids = data['mailIds'].split(',')
        print(mail_ids)

        output = move_mail_files(junk_folder, inbox_folder, mail_ids)
        return jsonify({'status': 'success', 'output': output})
    except Exception as e:
        print("Error:", str(e))  # Debugging information
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/get-mail-body', methods=['POST'])
def get_mail_body():
    try:
        data = request.json
        print("Received payload:", data)  # Debugging information

        junk_folder = r'C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\{}\Junk E-mail'.format(data['mailbox'])
        mail_file = os.path.join(junk_folder, data['mailFile'])
        details = extract_mai_info(mail_file)

        if not os.path.exists(mail_file):
            return jsonify({'status': 'error', 'error': 'Mail file not found'}), 404

        with open(mail_file, 'r') as file:
            lines = file.readlines()

        body = ''
        is_body = False
        for line in lines:
            if is_body:
                body += line
            if line.strip() == '':
                is_body = True
        tu = extract_mail_body(body)
        print('tu =', tu)
        autoresponse = ask(tu)
        response = {'status': 'success', 'body': tu, 'details': details, 'autoresponse': autoresponse}
        print(response)
        return response
    except Exception as e:
        print("Error:", str(e))  # Debugging information
        return jsonify({'status': 'error', 'error': str(e)}), 400

def extract_body(msg):
    soup = BeautifulSoup(msg, "html.parser")
    return soup.get_text()
def extract_mail_body(email_content):
   # Define the regular expression pattern to match the content within the body tag
    # Define the regular expression pattern to match from the first <div> to the last </div>
    pattern = re.compile(r'(<div[^>]*>.*</div>)', re.DOTALL)
    
    # Search for all matches in the file content
    matches = pattern.findall(email_content)
    
    if matches:
        # If matches are found, return the content from the first <div> to the last </div>
        return matches[0]
    else:
        # If no match is found, return an empty string or a suitable message
        return "No div content found"
    
def extract_mai_info(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:  # Assuming latin-1 encoding for .MAI files
        content = f.read()

    # Regex patterns for extracting headers
    from_pattern = re.compile(r"^From: (.+)$", re.MULTILINE)
    to_pattern = re.compile(r"^To: (.+)$", re.MULTILINE)
    sent_pattern = re.compile(r"^Date: (.+)$", re.MULTILINE)
    subject_pattern = re.compile(r"^Subject: (.+)$", re.MULTILINE)

    # Extracting data using regex
    from_match = from_pattern.search(content)
    to_match = to_pattern.search(content)
    sent_match = sent_pattern.search(content)
    subject_match = subject_pattern.search(content)

    # Initialize variables to store extracted values
    sender = from_match.group(1).strip() if from_match else None
    recipient = to_match.group(1).strip() if to_match else None
    sent_date = sent_match.group(1).strip() if sent_match else None
    email_subject = subject_match.group(1).strip() if subject_match else None

    return {
        'From': sender,
        'To': recipient,
        'Sent': sent_date,
        'Subject': email_subject
    }

def ask(mail):
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Generate an automatic one sentence response to this phishy mail to warn the phisher." + mail,
        }
    ],
    model="gpt-4-turbo",
)
    
    
    return chat_completion.choices[0].message.content


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
