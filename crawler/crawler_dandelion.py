__author__ = 'marcotagliabue'
import math
import logging

from dandelion import DataTXT

from dandelion.base import DandelionException

import configuration
from utils import mongo_manager
from model import tweets_chunk


class CrawlDandelion:
    def __init__(self, id_experiment, one_dandelion_key):
        if one_dandelion_key:
            self.run_crawler_one_keys(id_experiment)
        else:
            self.run_crawler_four_keys(id_experiment)

    def run_crawler_one_keys(self,id_experiment):
        self.id_experiment = id_experiment

        # Documentation: http://python-dandelion-eu.readthedocs.io/en/latest/datatxt.html#nex-named-entity-extraction
        self.db_manager = mongo_manager.MongoManager(configuration.db_name)
        languages = ("de", "en", "es", "fr", "it", "pt")

        all_tweets = list(self.db_manager.find("tweets", {"id_experiment":id_experiment}))

        tweets_each_request = math.ceil(len(all_tweets) / configuration.NUMBER_REQUEST_DANDELION)
        print(len(all_tweets), tweets_each_request)

        # Retrieve all tweets
        languages_chunks = []
        for l in languages:
            tweets = list(self.db_manager.find("tweets", {"lang": l, "id_experiment":id_experiment}))
            if (len(tweets) == 0):
                continue
            # print(l,len(tweets), len(tweets)%tweets_each_request)
            mod_tweets = tuple([tweets.pop() for i in range(0, len(tweets) % tweets_each_request)])
            # print(l,mod_tweets,len(tweets), len(tweets)%tweets_each_request)

            tweets_chunks = list(zip(*[iter(tweets)] * tweets_each_request))
            # print(len(tweets_chunks))
            if mod_tweets != ():
                tweets_chunks.append(mod_tweets)
            # print(len(tweets_chunks))

            languages_chunks.extend(tweets_chunks)

        self.run(languages_chunks, configuration.APP1_ID, configuration.API_KEY_DANDELION1)

    def run_crawler_four_keys(self,id_experiment):
        self.id_experiment = id_experiment

        # Documentation: http://python-dandelion-eu.readthedocs.io/en/latest/datatxt.html#nex-named-entity-extraction
        self.db_manager = mongo_manager.MongoManager(configuration.db_name)
        languages = ("de", "en", "es", "fr", "it", "pt")

        all_tweets = list(self.db_manager.find("tweets", {"id_experiment":id_experiment}))
        chunks_for_each_key = math.ceil(len(all_tweets) / 4)
        tweets_each_request = math.ceil(chunks_for_each_key / configuration.NUMBER_REQUEST_DANDELION)

        print(len(all_tweets), chunks_for_each_key, tweets_each_request)

        # Retrieve all tweets
        languages_chunks = []
        for l in languages:
            tweets = list(self.db_manager.find("tweets", {"lang": l, "id_experiment":id_experiment}))
            if (len(tweets) == 0):
                continue
            # print(l,len(tweets), len(tweets)%tweets_each_request)
            mod_tweets = tuple([tweets.pop() for i in range(0, len(tweets) % tweets_each_request)])
            # print(l,mod_tweets,len(tweets), len(tweets)%tweets_each_request)

            tweets_chunks = list(zip(*[iter(tweets)] * tweets_each_request))
            # print(len(tweets_chunks))
            if mod_tweets != ():
                tweets_chunks.append(mod_tweets)
            # print(len(tweets_chunks))

            languages_chunks.extend(tweets_chunks)

        self.split_tweets_and_run(languages_chunks)

    def split_tweets_and_run(self, tweets):
        size_chunk = math.ceil(len(tweets) / 4)

        # Run crawler with the 4 different Dandelion keys (Rate limit: 1000 req/day)
        self.run(tweets[:size_chunk], configuration.APP1_ID, configuration.API_KEY_DANDELION1)
        self.run(tweets[size_chunk:size_chunk * 2], configuration.APP2_ID, configuration.API_KEY_DANDELION2)
        self.run(tweets[size_chunk * 2:size_chunk * 3], configuration.APP3_ID, configuration.API_KEY_DANDELION3)
        self.run(tweets[size_chunk * 3:], configuration.APP4_ID, configuration.API_KEY_DANDELION4)

    def run(self, tweets_chunks, app_id, app_key):
        datatxt = DataTXT(app_id=app_id, app_key=app_key)
        for tweets in tweets_chunks:
            join_tweets = tweets_chunk.TweetsChunk(tweets)
            try:
                response = datatxt.nex(join_tweets.get_unique_string(), **{"lang": tweets[0]["lang"],
                                                                           "include": ["types", "categories",
                                                                                       "abstract", "alternate_labels"],
                                                                           "social.hashtag": True,
                                                                           "social.mention": True,
                                                                           "min_confidence":0})
                # print(response)
            except DandelionException as e:
                logging.error(e.code, e.message)
                continue
            join_tweets.split_annotation_each_tweet(response.annotations)
            # pprint.pprint(join_tweets.index_tweet)
            for tweet in join_tweets.index_tweet:
                seed_id = list(self.db_manager.find("seeds", {"handle": tweet["tweet"]["user"]["screen_name"], "id_experiment":self.id_experiment}))[0][
                    "_id"]
                for annotation in tweet["annotations"]:
                    annotation["tweet"] = tweet["tweet"]["_id"]
                    annotation["seed"] = seed_id
                    annotation["id_experiment"] = self.id_experiment
                    #print(annotation)
                    self.db_manager.write_mongo("entity", annotation)


if __name__ == "__main__":
    CrawlDandelion("1234")
