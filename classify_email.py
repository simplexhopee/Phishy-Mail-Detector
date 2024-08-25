import os
import re
from collections import Counter
from bs4 import BeautifulSoup
import joblib
import pandas as pd
from email import policy
from email.parser import BytesParser
import sys

# Load the trained model
model = joblib.load('stacking_model.pkl')

# Function to count characters
def count_characters(text):
    return len(text)

# Function to extract email domain
def get_email_domain(email):
    return email.split('@')[-1] if '@' in email else ''

# Function to find the most common URL
def most_common_url(urls):
    return Counter(urls).most_common(1)[0][0] if urls else ''

# Function to extract email content
def extract_msg(path, mail_file):
    with open(os.path.join(path, mail_file), 'r', encoding='utf-8') as file:
        msg = file.read()
    return msg

# Function to extract body content
def extract_body(msg):
    soup = BeautifulSoup(msg, "html.parser")
    return soup.get_text()

# Function to extract subject content
def extract_subj(msg):
    match = re.search(r'Subject: (.*)', msg)
    return match.group(1) if match else ''

# Function to extract sender address
def extract_send_address(msg):
    match = re.search(r'From: .* <(.*)>', msg)
    return match.group(1) if match else ''

# Function to extract reply-to address
def extract_replyTo_address(msg):
    match = re.search(r'Reply-To: .* <(.*)>', msg)
    return match.group(1) if match else ''

# Function to extract the most common URL
def extract_modal_url(msg):
    soup = BeautifulSoup(msg, "html.parser")
    urls = [a['href'] for a in soup.find_all('a', href=True)]
    return most_common_url(urls)

# Function to extract all links
def extract_all_links(msg):
    soup = BeautifulSoup(msg, "html.parser")
    return [a['href'] for a in soup.find_all('a', href=True)]

# Functions to extract body based attributes
def body_html(msg):
    return bool(BeautifulSoup(msg, "html.parser").find())

def body_forms(msg):
    return bool(BeautifulSoup(msg, "html.parser").find('form'))

def body_noWords(body_content):
    return len(body_content.split())

def body_noCharacters(body_content):
    return count_characters(body_content)

def body_noDistinctWords(body_content):
    return len(set(body_content.split()))

def body_richness(body_noWords, body_noCharacters):
    try:
        return float(body_noWords) / body_noCharacters
    except ZeroDivisionError:
        return 0

def body_noFunctionWords(body_content):
    function_words = ["account", "access", "bank", "credit", "click", "identity", "inconvenience", "information", "limited", "log", "minutes", "password", "recently", "risk", "social", "security", "service", "suspended"]
    return sum(body_content.lower().split().count(word) for word in function_words)

def body_suspension(body_content):
    return "suspension" in body_content.lower()

def body_verifyYourAccount(body_content):
    return "verify your account" in body_content.lower().replace(" ", "")

def extract_mail_body(email_content: str) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(email_content.encode())

    plain_text = None
    html_text = None

    def extract_parts(part):
        nonlocal plain_text, html_text
        if part.is_multipart():
            for subpart in part.iter_parts():
                extract_parts(subpart)
        else:
            content_type = part.get_content_type()
            charset = part.get_content_charset() or 'utf-8'
            if content_type == "text/plain":
                plain_text = part.get_payload(decode=True).decode(charset, errors="replace")
            elif content_type == "text/html":
                html_text = part.get_payload(decode=True).decode(charset, errors="replace")

    extract_parts(msg)
    
    return plain_text.strip() if plain_text else html_text.strip()

def extract_body_attributes(body_content):
    body_attributes = {
        'body_html': body_html(body_content),
        'body_forms': body_forms(body_content),
        'body_noWords': body_noWords(body_content),
        'body_noCharacters': body_noCharacters(body_content),
        'body_noDistinctWords': body_noDistinctWords(body_content),
        'body_richness': body_richness(body_noWords(body_content), body_noCharacters(body_content)),
        'body_noFunctionWords': body_noFunctionWords(body_content),
        'body_suspension': body_suspension(body_content),
        'body_verifyYourAccount': body_verifyYourAccount(body_content)
    }
    return body_attributes

# Functions to extract subject based attributes
def subj_reply(subj_content):
    return subj_content.lower().startswith("re:")

def subj_forward(subj_content):
    return subj_content.lower().startswith("fwd:")

def subj_noWords(subj_content):
    return len(subj_content.split())

def subj_noCharacters(subj_content):
    return count_characters(subj_content)

def subj_richness(subj_noWords, subj_noCharacters):
    try:
        return float(subj_noWords) / subj_noCharacters
    except ZeroDivisionError:
        return 0

def subj_allCaps(subj_content):
    return subj_content.isupper()

def subj_noFunctionWords(subj_content):
    function_words = ["account", "access", "bank", "credit", "click", "identity", "inconvenience", "information", "limited", "log", "minutes", "password", "recently", "risk", "social", "security", "service", "suspended"]
    return sum(subj_content.lower().split().count(word) for word in function_words)

def subj_suspension(subj_content):
    return "suspension" in subj_content.lower()

def subj_verifyYourAccount(subj_content):
    return "verify your account" in subj_content.lower().replace(" ", "")

def extract_subj_attributes(subj_content):
    subj_attributes = {
        'subj_reply': subj_reply(subj_content),
        'subj_forward': subj_forward(subj_content),
        'subj_noWords': subj_noWords(subj_content),
        'subj_noCharacters': subj_noCharacters(subj_content),
        'subj_richness': subj_richness(subj_noWords(subj_content), subj_noCharacters(subj_content)),
        'subj_allCaps': subj_allCaps(subj_content),
        'subj_noFunctionWords': subj_noFunctionWords(subj_content),
        'subj_suspension': subj_suspension(subj_content),
        'subj_verifyYourAccount': subj_verifyYourAccount(subj_content),
        'subj_bank': 'bank' in subj_content.lower()
    }
    return subj_attributes

# Functions to extract sender address based attributes
def send_diffSenderReplyTo(send_address, replyTo_address):
    return send_address != replyTo_address

def send_noWords(send_address):
    return len(send_address.split())

def send_noCharacters(send_address):
    return count_characters(send_address)

def send_nonModalSenderDomain(send_address):
    # This feature assumes the presence of a list of common domains to compare against
    common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com']
    domain = get_email_domain(send_address)
    return domain not in common_domains

def extract_send_attributes(send_address, replyTo_address):
    send_attributes = {
        'send_diffSenderReplyTo': send_diffSenderReplyTo(send_address, replyTo_address),
        'send_noCharacters': send_noCharacters(send_address),
        'send_noWords': send_noWords(send_address),
        'send_nonModalSenderDomain': send_nonModalSenderDomain(send_address)
    }
    return send_attributes

# Functions to extract URL based attributes
def url_atSymbol(url):
    return '@' in url

def url_noPeriods(url):
    return url.count('.')

def url_noDomains(links):
    return len(set(get_email_domain(link) for link in links))

def url_noExtLinks(links):
    return len([link for link in links if not link.startswith('/')])

def url_noImgLinks(links):
    return len([link for link in links if re.search(r'\.(jpg|jpeg|png|gif)$', link)])

def url_noIntLinks(links):
    return len([link for link in links if link.startswith('/')])

def url_noIpAddresses(links):
    return len([link for link in links if re.search(r'[0-9]+(?:\.[0-9]+){3}', link)])

def url_noPorts(links):
    return len([link for link in links if ':' in link])

def url_nonModalHereLinks(links):
    # Assuming this feature identifies if the word 'here' is a link text
    if (len([link for link in links if 'here' in link]) > 0):
        return True
    return False

def extract_url_attributes(url, links):
    url_attributes = {
        'url_atSymbol': url_atSymbol(url),
        'url_noPeriods': url_noPeriods(url),
        'url_noDomains': url_noDomains(links),
        'url_noExtLinks': url_noExtLinks(links),
        'url_noImgLinks': url_noImgLinks(links),
        'url_noIntLinks': url_noIntLinks(links),
        'url_noIpAddresses': url_noIpAddresses(links),
        'url_noPorts': url_noPorts(links),
        'url_nonModalHereLinks': url_nonModalHereLinks(links)
    }
    return url_attributes

# Functions to extract script based attributes
def contains_script(msg):
    return bool(BeautifulSoup(msg, "html.parser").findAll('script'))

def contains_external_script(msg):
    return bool(BeautifulSoup(msg, "html.parser").findAll('script', src=True))

def script_noScriptBlocks(msg):
    return len(BeautifulSoup(msg, "html.parser").findAll('script'))

def script_noWords(msg):
    return sum(len(script.string.split()) for script in BeautifulSoup(msg, "html.parser").findAll('script') if script.string)

def script_noCharacters(msg):
    return sum(count_characters(script.string) for script in BeautifulSoup(msg, "html.parser").findAll('script') if script.string)

def script_richness(script_noWords, script_noCharacters):
    try:
        return float(script_noWords) / script_noCharacters
    except ZeroDivisionError:
        return 0

def extract_script_attributes(msg):
    scripts = BeautifulSoup(msg, "html.parser").findAll('script')
    script_content = ' '.join(script.string for script in scripts if script.string)
    script_attributes = {
        'contains_script': contains_script(msg),
        'contains_external_script': contains_external_script(msg),
        'script_noScriptBlocks': script_noScriptBlocks(msg),
        'script_noWords': script_noWords(script_content),
        'script_noCharacters': script_noCharacters(script_content),
        'script_richness': script_richness(script_noWords(script_content), script_noCharacters(script_content))
    }
    return script_attributes
def extract_urls(email_body):
    # Regex to find URLs in the email body
    urls = re.findall(r'(https?://\S+)', email_body)
    return urls

def extract_url_link_text(email_body):
    urls = extract_urls(email_body)
    link_texts = [re.findall(r'<a [^>]*>(.*?)</a>', url) for url in urls]
    link_texts = [text for sublist in link_texts for text in sublist]  # Flatten the list
    return len(link_texts)

def extract_url_max_no_periods(email_body):
    urls = extract_urls(email_body)
    max_no_periods = max([url.count('.') for url in urls], default=0)
    return max_no_periods

def extract_url_no_links(email_body):
    urls = extract_urls(email_body)
    return len(urls)

def extract_url_ports(email_body):
    urls = extract_urls(email_body)
    ports = [re.findall(r':[0-9]+', url) for url in urls]
    ports = [port for sublist in ports for port in sublist]  # Flatten the list
    if (len(ports) > 0):
        return True
    return False

# Overall feature extraction function
def overall_feature_extraction(path, mail_file):
    msg = extract_msg(path, mail_file)
    body_first = extract_body(msg)
    body_content = extract_mail_body(body_first)
    
    subj_content = extract_subj(msg)
    send_address = extract_send_address(msg)
    replyTo_address = extract_replyTo_address(msg)
    url = extract_modal_url(msg)
    links = extract_all_links(msg)

    body_attributes = extract_body_attributes(body_content)
    
    subj_attributes = extract_subj_attributes(subj_content)
    send_attributes = extract_send_attributes(send_address, replyTo_address)
    url_attributes = extract_url_attributes(url, links)
    script_attributes = extract_script_attributes(msg)
    
    features = {**body_attributes, **subj_attributes, **send_attributes, **url_attributes, **script_attributes}
    # Extract url_linkText
    features['url_linkText'] = extract_url_link_text(mail_file)
    
    # Extract url_maxNoPeriods
    features['url_maxNoPeriods'] = extract_url_max_no_periods(mail_file)
    
    # Extract url_noLinks
    features['url_noLinks'] = extract_url_no_links(mail_file)
    
    # Extract url_ports
    features['url_ports'] = extract_url_ports(mail_file)
    
        
    return features

# Function to classify an incoming email
def classify_email(path, email_file):
    # Extract features from the email
    email_features = overall_feature_extraction(path, email_file)
  
    
    # Prepare the features for the model (make sure it matches the features used during training)
    feature_names = [
        'body_forms', 'body_html', 'body_noCharacters', 'body_noDistinctWords', 'body_noFunctionWords', 'body_noWords', 'body_richness', 'body_suspension', 'body_verifyYourAccount',
        'send_diffSenderReplyTo', 'send_noCharacters', 'send_noWords', 'send_nonModalSenderDomain', 
        'subj_bank', 'subj_noCharacters', 'subj_noWords', 'subj_reply', 'subj_richness', 
        'url_atSymbol', 'url_linkText', 'url_maxNoPeriods', 'url_noDomains', 'url_noExtLinks', 'url_noImgLinks', 'url_noIntLinks', 'url_noIpAddresses', 'url_noLinks', 'url_noPorts', 'url_nonModalHereLinks', 'url_ports'
    ]
    
    # Ensure all required features are present
    missing_features = [feature for feature in feature_names if feature in email_features]
    
    email_data = [email_features[feature] for feature in feature_names]

        # Convert the email data to a DataFrame with appropriate feature names
    email_df = pd.DataFrame([email_data], columns=feature_names)
    pd.set_option('display.max_columns', None)
    
    
    # Classify the email
    classification_result = model.predict(email_df)[0]
    # Print the email body
    # Print the classification result (this is what the batch script captures)
    print(classification_result)

    return classification_result

if __name__ == "__main__":
    email_path = r'C:\Program Files (x86)\Mail Enable\Queues\SMTP\Inbound\Messages'
    email_file = sys.argv[1]
    classify_email(email_path, email_file)