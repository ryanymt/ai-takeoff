# Extract Entities and Analyse Sentiment with Natural Language API

## Objectives
In this lab, you will learn how to:

1. Create a Natural Language API request and calling the API with curl

2. Extract entities and running sentiment analysis on text with the Natural Language API
    
3. Perform linguistic analysis on text with the Natural Language API
    
4. Create a Natural Language API request in a different language

## Task 1. Create an API key
Since you use ```curl``` to send a request to the Natural Language API, you must generate an API key to pass in your request URL.

1.  To create an API key, in the Cloud Console, select **Navigation menu > APIs & Services > Credentials**.
    
2.  Click **Create credentials** and select **API key**.
    
3.  **Copy** the generated API key and click **Close**.
    
In order to perform next steps please connect to **Cloud Shell**:

1.  You will use **Cloud Shell**, a command-line environment running in Google Cloud 

2. From the Cloud Console, click **Activate Cloud Shell** on the top right corner
    
3.  In the command line, enter in the following, replacing ```<YOUR_API_KEY>``` with the key you just copied:

```bash
export API_KEY=<YOUR_API_KEY>
```

## Task 2. Make an entity analysis request

The first Natural Language API method you use is **analyzeEntities**. With this method, the API can extract entities (like people, places, and events) from text. To try it out the API's entity analysis, use the following sentence:

> Joanne Rowling, who writes under the pen names J. K. Rowling and Robert Galbraith, is a British novelist and screenwriter who wrote the Harry Potter fantasy series.

You build your request to the Natural Language API in the file named ```request.json```.

1.  Use nano (a code editor) to create the file ```request.json```:

```bash
nano request.json
```

2. Type or paste the following code into ```request.json```:

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"Joanne Rowling, who writes under the pen names J. K. Rowling and Robert Galbraith, is a British novelist and screenwriter who wrote the Harry Potter fantasy series."
  },
  "encodingType":"UTF8"
}
```
3.  Press ```CTRL+X``` to exit nano, then ```Y``` to save the file, then ```ENTER``` to confirm.
    

In the request, you're telling the Natural Language API about the text being sent. Supported type values are ```PLAIN_TEXT``` or ```HTML```. In content, you pass the text to send to the Natural Language API for analysis.

The Natural Language API also supports sending files stored in Cloud Storage for text processing. If you wanted to send a file from Cloud Storage, you would replace content with ```gcsContentUri``` and give it a value of the text file's uri in Cloud Storage.

```encodingType``` tells the API which type of text encoding to use when processing our text. The API will use this to calculate where specific entities appear in our text.

## Task 3. Call the Natural Language API

1.  You can now pass your request body, along with the API key environment variable you saved earlier, to the Natural Language API with the following curl command (all in one single command line):

```bash
curl  "https://language.googleapis.com/v1/documents:analyzeEntities?key=${API_KEY}"  \

-s  -X  POST  -H  "Content-Type:  application/json"  --data-binary  @request.json  >  result.json
```

2.  In order to check the response run:
```bash
cat result.json
```

The beginning of your response should look like this:
```json
"content": "Joanne Rowling",
            "beginOffset": 0
          },
          "type": "PROPER"
        },
        {
          "text": {
            "content": "Rowling",
            "beginOffset": 53
          },
          "type": "PROPER"
        },
        {
          "text": {
            "content": "novelist",
            "beginOffset": 96
          },
          "type": "COMMON"
        },
        {
          "text": {
            "content": "Robert Galbraith",
            "beginOffset": 65
          },
          "type": "PROPER"
        }
      ]
    },

    ...
  ]
}
```

For each entity in the response, you get the entity type, the associated Wikipedia URL if there is one, the salience, and the indices of where this entity appeared in the text. Salience is a number in the [0,1] range that refers to the centrality of the entity to the text as a whole.

The Natural Language API can also recognize the same entity mentioned in different ways. Take a look at the mentions list in the response: the API is able to tell that "Joanne Rowling", "Rowling", "novelist" and "Robert Galbriath" all point to the same thing.


## Task 4. Sentiment analysis with the Natural Language API

In addition to extracting entities, the Natural Language API also lets you perform sentiment analysis on a block of text. This JSON request will include the same parameters as the request above, but this time change the text to include something with a stronger sentiment.

1.  Remove the previous ```request.json``` file

```bash
rm request.json
```

2. and create a new file with this code:

```bash
nano request.json
```

Paste

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"Harry Potter is the best book. I think everyone should read it."
  },
  "encodingType": "UTF8"
}
```

3. Press ```CTRL+X``` to exit nano, then ```Y``` to save the file, then ```ENTER``` to confirm.

4. Next you send the request to the API's ```analyzeSentiment``` endpoint:


```bash
curl "https://language.googleapis.com/v1/documents:analyzeSentiment?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request.json
```


Your response should look like this:


```json
{
  "documentSentiment": {
    "magnitude": 1.9,
    "score": 0.9
  },
  "language": "en",
  "sentences": [
    {
      "text": {
        "content": "Harry Potter is the best book.",
        "beginOffset": 0
      },
      "sentiment": {
        "magnitude": 0.9,
        "score": 0.9
      }
    },
    {
      "text": {
        "content": "I think everyone should read it.",
        "beginOffset": 31
      },
      "sentiment": {
        "magnitude": 0.9,
        "score": 0.9
      }
    }
  ]
}
```


Note: Don't be alarmed if your scores differ slightly than the example output.

Notice that you get two types of sentiment values: sentiment for the document as a whole, and sentiment broken down by sentence. The sentiment method returns two values:

-   ```score``` - is a number from -1.0 to 1.0 indicating how positive or negative the statement is.
    
-   ```magnitude``` - is a number ranging from 0 to infinity that represents the weight of sentiment expressed in the statement, regardless of being positive or negative.
    

Longer blocks of text with heavily weighted statements have higher magnitude values. The score for the first sentence is positive (0.7), whereas the score for the second sentence is neutral (0.1).


## Task 5. Analyzing entity sentiment

In addition to providing sentiment details on the entire text document, the Natural Language API can also break down sentiment by the entities in the text. Use this sentence as an example:

> "I liked the sushi but the service was terrible."


In this case, getting a sentiment score for the entire sentence as you did above might not be so useful. If this was a restaurant review and there were hundreds of reviews for the same restaurant, you'd want to know exactly which things people liked and didn't like in their reviews. Fortunately, the Natural Language API has a method that lets you get the sentiment for each entity in the text, called analyzeEntitySentiment. Let's see how it works!
Use nano to update request.json with the sentence below:

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"I liked the sushi but the service was terrible."
  },
  "encodingType": "UTF8"
}
```


2.  Press ```CTRL+X``` to exit nano, then ```Y``` to save the file, then ```ENTER``` to confirm.
    
3. Then call the ```analyzeEntitySentiment``` endpoint with the following ```curl``` command:


```bash
curl  "https://language.googleapis.com/v1/documents:analyzeEntitySentiment?key=${API_KEY}"  \

-s  -X  POST  -H  "Content-Type:  application/json"  --data-binary  @request.json
```


In the response you get back two entity objects: one for ```"sushi"``` and one for ```"service"```. Here's the full JSON response:


```json
{
  "entities": [
    {
      "name": "sushi",
      "type": "CONSUMER_GOOD",
      "metadata": {},
      "salience": 0.51064336,
      "mentions": [
        {
          "text": {
            "content": "sushi",
            "beginOffset": 12
          },
          "type": "COMMON",
          "sentiment": {
            "magnitude": 0,
            "score": 0
          }
        }
      ],
      "sentiment": {
        "magnitude": 0,
        "score": 0
      }
    },
    {
      "name": "service",
      "type": "OTHER",
      "metadata": {},
      "salience": 0.48935664,
      "mentions": [
        {
          "text": {
            "content": "service",
            "beginOffset": 26
          },
          "type": "COMMON",
          "sentiment": {
            "magnitude": 0.7,
            "score": -0.7
          }
        }
      ],
      "sentiment": {
        "magnitude": 0.7,
        "score": -0.7
      }
    }
  ],
  "language": "en"
}
```


You can see that the score returned for ```"sushi"``` was a neutral score of 0, whereas ```"service"``` got a score of -0.7. Cool! You also may notice that there are two sentiment objects returned for each entity. If either of these terms were mentioned more than once, the API would return a different sentiment score and magnitude for each mention, along with an aggregate sentiment for the entity.

Note: Don't be alarmed if your scores differ slightly than the example output.

## Task 6. Multilingual natural language processing
The Natural Language API also supports languages other than English (full list can be found in the [Language Support Guide](https://cloud.google.com/natural-language/docs/languages)).

1.  Modify the code in ```request.json``` with a sentence in Japanese:

```json
{

"document":{

"type":"PLAIN_TEXT",

"content":"日本のグーグルのオフィスは、東京の六本木ヒルズにあります"

}

}
```


2.  Press ```CTRL+X``` to exit nano, then ```Y``` to save the file, then ```ENTER``` to confirm.
    

Notice that you didn't tell the API which language the text is, it can automatically detect it!

3.  Next, you send it to the ```analyzeEntities``` endpoint:

```bash
curl  "https://language.googleapis.com/v1/documents:analyzeEntities?key=${API_KEY}"  \

-s  -X  POST  -H  "Content-Type:  application/json"  --data-binary  @request.json
```

And you get the following response:


```json
{
  "entities": [
    {
      "name": "日本",
      "type": "LOCATION",
      "metadata": {
        "mid": "/m/03_3d",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Japan"
      },
      "salience": 0.23854347,
      "mentions": [
        {
          "text": {
            "content": "日本",
            "beginOffset": 0
          },
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "グーグル",
      "type": "ORGANIZATION",
      "metadata": {
        "mid": "/m/045c7b",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Google"
      },
      "salience": 0.21155767,
      "mentions": [
        {
          "text": {
            "content": "グーグル",
            "beginOffset": 9
          },
          "type": "PROPER"
        }
      ]
    },
    ...
  ]
  "language": "ja"
}
```

The wikipedia URLs even point to the Japanese Wikipedia pages!