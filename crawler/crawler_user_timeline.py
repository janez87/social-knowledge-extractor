__author__ = 'marcotagliabue'
# PROBLEM: http://www.craigaddyman.com/mining-all-tweets-with-python/

import configuration
from twython import Twython, TwythonAuthError, TwythonError
import logging
from langdetect import detect


class CrawlerUserTimelineTwitter:
    def __init__(self):
        self.languages = ("de", "en", "es", "fr", "it", "pt")
        self.max_tweets_retrievable = 3200
        self.max_per_request = 200
        self.twitter = Twython(configuration.consumer_key, configuration.consumer_secret, configuration.access_token,
                               configuration.access_token_secret)

    def get_users_tweets(self, screen_name, N):
        """
        :param screen_name: Twitter username
        :param N: Number of tweets of User
        :return: N tweets
        """
        try:
            user_tweets = []
            if N >= self.max_tweets_retrievable:
                N = self.max_tweets_retrievable
                iteration = 16
            else:
                iteration, last_count = divmod(N, self.max_per_request)
                iteration += 1

                user_timeline = self.twitter.get_user_timeline(screen_name=screen_name, count=1)

                if (user_timeline):
                    ##the latest starting tweet id
                    lis = [int(user_timeline[0]["id_str"])]

                    ## iterate through all tweets: Max 3200 for each user
                    for i in range(0, iteration):

                        ## tweet extract method with the last list item as the max_id
                        user_timeline = self.twitter.get_user_timeline(screen_name=screen_name,
                                                                       count=self.max_per_request,
                                                                       include_retweets=False,
                                                                       max_id=lis[-1])
                        for tweet in user_timeline:
                            # Check if seed Name is different from screen_name tweet
                            # if(screen_name != tweet["user"]["screen_name"]):
                            #    print(screen_name,tweet["user"]["screen_name"] )

                            if (tweet["lang"] == None):
                                tweet["lang"] = detect(tweet["text"].replace("\n", " "))

                            if (tweet["lang"] in self.languages):
                                user_tweets.append(tweet)
                                # print(tweet) ## print the tweet
                                lis.append(tweet['id'])  ## append tweet id's

                    return user_tweets[:N]
                else:
                    return []

        except TwythonAuthError as e:
            # Manage Suspended Item
            logging.error(e)
            return []
        except TwythonError as e:
            logging.error(e.error_code)
            # Manage No Page Found: User Doesn't exist
            return []

    def get_all_handles_mentioned(self, list_of_tweet, owner):

        mentions = []
        for tweet in list_of_tweet:
            mentions.extend([mention["screen_name"] for mention in tweet["entities"]["user_mentions"]])

        mentions_unique = list(set(mentions))

        if owner in mentions_unique:
            mentions_unique.remove(owner)

        return mentions_unique
