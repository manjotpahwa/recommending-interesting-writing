import json
import numpy as np
import boto3


def getData():
    BUCKET = 'personal-bucket-news-ranking'
    FILE_TO_READ = 'pub_emb+bias.json'
   client = boto3.client('s3',
                           aws_access_key_id='xxxxxxxxxxxxxxxxxxxx',
                           aws_secret_access_key='xxxxxxxxxxxxxxxxxxx'
                         )
    result = client.get_object(Bucket=BUCKET, Key=FILE_TO_READ)
    publications = json.loads(result["Body"].read().decode())

    FILE_TO_READ = 'select_demo_articles.json'
    result = client.get_object(Bucket=BUCKET, Key=FILE_TO_READ)
    articles = json.loads(result["Body"].read().decode())

    FILE_TO_READ = 'word_to_emb+bias_dict.json'
    result = client.get_object(Bucket=BUCKET, Key=FILE_TO_READ)
    words = json.loads(result["Body"].read().decode())

    return publications, articles, words


def hello(event, context):
    publications, articles, words = getData()

    print("Data Loaded!")
    current_pub_embedding = np.array(publications['embedding'])
    current_pub_embedding[1] = event['a']
    current_pub_embedding[5] = event['b']
    current_pub_embedding[17] = event['c']
    current_pub_embedding[34] = event['d']
    current_pub_embedding[67] = event['e']
    print(current_pub_embedding)
    list_of_logits = []
    for item in articles:
        word_emb_product_sum = 0
        word_count = 0
        word_list = []
        word_logit_list = []
        for word in item['text']:
            if word in words.keys() and word not in word_list:
                word_count += 1
                word_emb_product = float(np.dot(current_pub_embedding,
                                                np.array(words[word]['embedding']))) + words[word]['bias']
                word_emb_product_sum += word_emb_product
                word_list.append(word)
                word_logit_list.append(word_emb_product)

        indices = np.argsort(word_logit_list)[::-1]

        top_words = []
        for idx in range(10):
            current_idx = indices[idx]
            current_word = word_list[current_idx]
            current_logit = word_logit_list[current_idx]
            top_words.append({"word": current_word, "contribution": current_logit})

        least_words = []
        for idx in range(10):
            current_idx = indices[len(indices)-1-idx]
            current_word = word_list[current_idx]
            current_logit = word_logit_list[current_idx]
            least_words.append({"word": current_word, "contribution": current_logit})

        word_emb_product_mean = word_emb_product_sum/word_count
        article_logit = word_emb_product_mean + publications['bias']
        item['logit'] = article_logit
        item['top_words'] = top_words
        item['least_words'] = least_words
        list_of_logits.append(article_logit)

    print("Logits Generated")

    top_article_dict = []
    indices = np.argsort(list_of_logits)[::-1]
    for top_idx in range(75):
        article = articles[indices[top_idx]]
        top_article_dict.append(article)

    response = {
        "statusCode": 200,
        "body": json.dumps(top_article_dict)
    }

    return response


if __name__ == "__main__":
    test_dict = {'a': .2, 'b': 5, 'c': 100, "d": -24, "e": -37}
    hello(test_dict, '')
