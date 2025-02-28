import os
import tweepy
from flask import Flask, request, render_template_string
from dotenv import load_dotenv

# Load API credentials from Replit Secrets
load_dotenv()
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")  # Added for v2 API

# Check if all credentials are present
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    print("WARNING: One or more Twitter API credentials are missing!")

# Authenticate with Twitter v2 API
try:
    # For v2 API we use Client instead of API
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY, 
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN, 
        access_token_secret=ACCESS_SECRET
    )
    # Verify connection (get user info)
    user_info = client.get_me()
    if user_info.data:
        print(f"Twitter authentication successful! Logged in as: @{user_info.data.username}")
except Exception as e:
    print(f"Twitter authentication failed: {str(e)}")
    # Create a client that will fail gracefully
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN or "",
        consumer_key=API_KEY or "", 
        consumer_secret=API_SECRET or "",
        access_token=ACCESS_TOKEN or "", 
        access_token_secret=ACCESS_SECRET or ""
    )

# Flask app setup
app = Flask(__name__)

# HTML template with CSS styling
template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F3 Isotope Tweet Sender</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #fcfafa; /* subtle red background */
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-top: 40px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            max-width: 150px;
            margin-bottom: 10px;
        }
        h1 {
            color: #000000;
            margin: 10px 0;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #14171a;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccd6dd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        .btn-submit {
            background-color: #ff0000;
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 16px;
            border-radius: 100px;
            cursor: pointer;
            width: 100%;
            font-weight: bold;
        }
        .btn-submit:hover {
            background-color: #c20202;
        }
        .message {
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
        }
        .success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #a5d6a7;
            margin-bottom: 20px;
        }
        .error {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef9a9a;
            margin-bottom: 20px;
        }
        .preview {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
        }
        .char-counter {
            font-size: 14px;
            margin-top: 5px;
            text-align: right;
            color: green;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://i.ibb.co/FLgZNnBM/f3isotope-header.png" alt="F3 Isotope Logo" class="logo" style="cursor: pointer;" id="logoReset">
            <h1>Preblast on X</h1>
        </div>

        {% if message %}
        <div class="message {% if 'Error' in message %}error{% else %}success{% endif %}">
            {{ message|safe }}
        </div>
        {% endif %}

        <form method="post">
            <div class="form-group">
                <label for="q">Q (F3 Nickname):</label>
                <input type="text" id="q" name="q" required value="{{ q or '' }}">
            </div>

            <div class="form-group">
                <label for="twitter_handle">Q's Twitter Account (optional):</label>
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 5px; font-size: 16px;">@</span>
                    <input type="text" id="twitter_handle" name="twitter_handle" placeholder="Without @ symbol" value="{{ twitter_handle or '' }}">
                </div>
            </div>

            <div class="form-group">
                <label for="workout_name">Workout Name:</label>
                <input type="text" id="workout_name" name="workout_name" required value="{{ workout_name or '' }}">
            </div>

            <div class="form-group">
                <label for="message">Message:</label>
                <textarea id="message" name="message" required>{{ message_content or '' }}</textarea>
            </div>

            <div class="preview" id="preview" style="display: none;">
                <strong>Tweet Preview:</strong>
                <p id="preview-text"></p>
            </div>

            <button type="submit" class="btn-submit" id="submitButton">Send Tweet</button>
        </form>
    </div>

    <script>
        // Live preview functionality and character counting
        const qInput = document.getElementById('q');
        const twitterHandleInput = document.getElementById('twitter_handle');
        const workoutInput = document.getElementById('workout_name');
        const messageInput = document.getElementById('message');
        const preview = document.getElementById('preview');
        const previewText = document.getElementById('preview-text');
        const submitButton = document.getElementById('submitButton');
        const MAX_TWEET_LENGTH = 280;
        let charCounter;

        // Create character counter element
        function createCharCounter() {
            charCounter = document.createElement('div');
            charCounter.className = 'char-counter';
            const messageGroup = messageInput.parentElement;
            messageGroup.appendChild(charCounter);
        }
        createCharCounter();

        // Twitter handle validation
        twitterHandleInput.addEventListener('input', function() {
            // Remove @ if user includes it
            if (this.value.startsWith('@')) {
                this.value = this.value.substring(1);
            }

            // Basic Twitter handle validation (alphanumeric and underscore only)
            const twitterRegex = /^[A-Za-z0-9_]*$/;
            if (this.value && !twitterRegex.test(this.value)) {
                this.setCustomValidity("Twitter handle can only contain letters, numbers, and underscores.");
            } else {
                this.setCustomValidity("");
            }
        });

        function calculateTweetLength(q, twitterHandle, workoutHashtag, msg) {
            // Use Twitter handle if provided, otherwise use Q name
            const qLeader = twitterHandle ? `@${twitterHandle}` : q;

            // Calculate exact tweet length with the template
            return `Hey @f3isotope pax!
${qLeader} is leading #${workoutHashtag}.
${msg} #pb`.length;
        }

        function updatePreview() {
            const q = qInput.value.trim();
            const twitterHandle = twitterHandleInput.value.trim();
            const workout = workoutInput.value.trim();
            const msg = messageInput.value.trim();
            const workoutHashtag = workout.replace(/ /g, '');

            // Determine leader text (Twitter handle or Q name)
            const qLeader = twitterHandle ? `@${twitterHandle}` : q;

            // Calculate remaining characters
            const currentLength = calculateTweetLength(q || '', twitterHandle || '', workoutHashtag || '', msg || '');
            const remaining = MAX_TWEET_LENGTH - currentLength;

            // Update character counter
            charCounter.textContent = `${currentLength}/${MAX_TWEET_LENGTH} characters (${remaining} remaining)`;

            // Set color based on remaining characters
            if (remaining < 0) {
                charCounter.style.color = 'red';
                charCounter.textContent += " - Tweet is too long!";
                messageInput.setCustomValidity("A tweet is limited to 280 characters. Please adjust your message to fit.");
            } else if (remaining < 20) {
                charCounter.style.color = 'orange';
                messageInput.setCustomValidity("");
            } else {
                charCounter.style.color = 'green';
                messageInput.setCustomValidity("");
            }

            if (q || workout || msg) {
                preview.style.display = 'block';
                previewText.innerText = `Hey @f3isotope pax!\n${qLeader || '[Q name]'} is leading #${workoutHashtag || '[workout]'}.\n${msg || '[message]'} #pb`;
            } else {
                preview.style.display = 'none';
            }
        }

        qInput.addEventListener('input', updatePreview);
        twitterHandleInput.addEventListener('input', updatePreview);
        workoutInput.addEventListener('input', updatePreview);
        messageInput.addEventListener('input', updatePreview);

        // Update preview on page load if values exist
        window.addEventListener('load', updatePreview);

        // Add reset functionality to logo
        document.getElementById('logoReset').addEventListener('click', function() {
            // Clear all form fields
            qInput.value = '';
            twitterHandleInput.value = '';
            workoutInput.value = '';
            messageInput.value = '';

            // Clear any validation messages
            qInput.setCustomValidity('');
            twitterHandleInput.setCustomValidity('');
            workoutInput.setCustomValidity('');
            messageInput.setCustomValidity('');

            // Hide preview
            preview.style.display = 'none';

            // Hide character counter instead of updating it
            charCounter.textContent = '';

            // Remove success/error messages
            const messages = document.querySelectorAll('.message');
            messages.forEach(msg => msg.style.display = 'none');
            
            // Re-enable the submit button
            submitButton.disabled = false;
            submitButton.textContent = "Send Tweet";
            submitButton.style.opacity = "1";
        });
        
        // Check if there's a success message and disable the button if tweet was successful
        window.addEventListener('load', function() {
            const messageDiv = document.querySelector('.message.success');
            if (messageDiv && messageDiv.innerHTML.includes('Tweet successfully posted')) {
                // Disable the button after successful tweet
                submitButton.disabled = true;
                submitButton.textContent = "Tweet Sent ✓";
                submitButton.style.opacity = "0.7";
            }
        });
        
        // Add form submission handler to disable button
        document.querySelector('form').addEventListener('submit', function() {
            // Disable button to prevent multiple submissions
            submitButton.disabled = true;
            submitButton.textContent = "Sending...";
            submitButton.style.opacity = "0.7";
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def tweet_form():
    alert_message = None
    q_val = ''
    twitter_handle_val = ''
    workout_name_val = ''
    message_val = ''

    if request.method == 'POST':
        q_val = request.form.get('q', '')
        twitter_handle_val = request.form.get('twitter_handle', '').strip()
        workout_name_val = request.form.get('workout_name', '')
        message_val = request.form.get('message', '')

        if not q_val or not workout_name_val or not message_val:
            alert_message = "All fields (Q, Workout Name, Message) are required!"
        else:
            # Format the tweet with spaces removed from hashtag
            workout_hashtag = workout_name_val.replace(" ", "")

            # Use Twitter handle if provided, otherwise use Q name
            q_leader = f"@{twitter_handle_val}" if twitter_handle_val else q_val

            tweet = f"Hey @f3isotope pax!\n{q_leader} is leading #{workout_hashtag}.\n{message_val} #pb"

            # Check tweet length
            if len(tweet) > 280:
                alert_message = "Error: Tweet exceeds 280 character limit. Please adjust your message."
            else:
                try:
                    # Using client.create_tweet instead of api.update_status for v2 API
                    response = client.create_tweet(text=tweet)
                    if response.data and 'id' in response.data:
                        tweet_id = response.data['id']
                        # Get Twitter username directly from globals or use a generic link
                        try:
                            if 'user_info' in globals() and hasattr(user_info, 'data') and hasattr(user_info.data, 'username'):
                                username = user_info.data.username
                                tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
                                alert_message = f'Tweet successfully posted! <a href="{tweet_url}" target="_blank">View on X</a>'
                            else:
                                # Generic tweet URL if username isn't available
                                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
                                alert_message = f'Tweet successfully posted! <a href="{tweet_url}" target="_blank">View on X</a>'
                        except Exception:
                            # If any error occurs, just show success without link
                            alert_message = "Tweet successfully posted!"
                    else:
                        alert_message = "Tweet successfully posted!"
                except Exception as e:
                    alert_message = f"Error posting tweet: {str(e)}"

    # Avoid the naming conflict by using different parameter names
    return render_template_string(
        template, 
        message=alert_message, 
        q=q_val, 
        twitter_handle=twitter_handle_val, 
        workout_name=workout_name_val, 
        message_content=message_val
    )

if __name__ == '__main__':
    # Use debug mode only in development, not in production
    debug_mode = os.environ.get('ENVIRONMENT') != 'production'
    app.run(host='0.0.0.0', port=8080, debug=debug_mode)