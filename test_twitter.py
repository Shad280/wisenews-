import tweepy

# Test script to verify Twitter API access
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAFOc3QEAAAAAwFWgGM%2FJnepYkyVyrsn5WZzcMRI%3DQtDxII81yUK8iqMygdKw72WP8N3q36piLtJPSpCic1qEig4Jea"  # Replace with your real token

def test_twitter_api():
    try:
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        
        # Test by getting a few tweets from CNN
        print("🔄 Attempting to connect to Twitter API...")
        tweets = client.get_users_tweets(id="759251", max_results=5)
        
        if tweets.data:
            print("✅ Twitter API is working!")
            print(f"Retrieved {len(tweets.data)} tweets from CNN")
            for tweet in tweets.data:
                print(f"- {tweet.text[:100]}...")
        else:
            print("❌ No tweets returned - check your setup")
            
    except tweepy.Unauthorized as e:
        print(f"❌ Unauthorized Error: {e}")
        print("This means your Bearer Token is invalid, expired, or doesn't have proper permissions")
        print("You need to get a new Bearer Token from Twitter Developer Portal")
    except tweepy.TooManyRequests as e:
        print(f"❌ Rate Limit Error: {e}")
        print("You've hit the rate limit. Wait and try again later.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Check your Bearer Token and internet connection")

if __name__ == "__main__":
    test_twitter_api()
