# How to setup the server

Fill the needed data inside the `instance/config.toml` file.  
Then, you can use `docker compose` to run the development server

```
docker compose up -d --build
```

# How to use the `transcribe` api

You can use the following curl request to transcribe a video

```
`curl -X POST "http://localhost:5000/api/transcribe" \
  -H "X-API-PASSCODE: YOUR_PASSCODE" \
  -F "video=@/absolute/path/to/video.mp4" \
  -F "language=it"`
```

with `YOUR_PASSCODE` being the `secret_passcode` set in the `API` section of `instance/config.toml`. 
For the video, you can use one of the videos provided in the `sample_videos/`.  
In this case the video is loaded from the filesystem. However, it can also be sent as a part of the HTTPS request.

# How to use the `generate_qa` api

For example, you can use the following curl request

```
curl -X POST "http://localhost:5000/api/generate_qa" \  
  -H "X-API-PASSCODE: YOUR_PASSCODE" \  
  -F "language=it" \  
  -F "competency_level=medium" \  
  -F "num_questions=10" \  
  -F "num_multiple_answers=4" \  
  -F "topic=Alessandro Magno" \  
  -F "transcription=<transcription_example.json"  
```

with `YOUR_PASSCODE` being the `secret_passcode` set in the `API` section of `instance/config.toml`.  
The request will return a list of dictionaries, each containing the question text, the possible answers, and the position (in python indexing) of the correct answer.

# How to use the `evaluate` api

```
curl -X POST "http://localhost:5000/api/evaluate" \  
  -H "X-API-PASSCODE: YOUR_PASSCODE" \  
  -F "language=it" \  
  -F "competency_level=medium" \  
  -F "topic=Alessandro Magno" \  
  -F "transcription=<transcription_example.json" \  
  -F "questions=<questions.json" \  
  -F "user_answers=<user_answers.json" \  
  -F "correct_answers=<correct_answers.json"  
```

with `YOUR_PASSCODE` being the `secret_passcode` set in the `API` section of `instance/config.toml`.  
The request will return the list of correct answers, the weak topics identified and a feedback message indicating which part needs to be revised.  

# How to provide multiple documents / syllabus

To provide multiple documents or syllabus to the APIs, just append the following attributes to the previous `generate_qa` / `evaluate` requests

```
  -F "document=@/path/to/document1.pdf"
  -F "document=@/path/to/document2.pdf"
```

for the syllabus,

```
  -F "syllabus=@/path/to/syllabus1.pdf"
  -F "syllabus=@/path/to/syllabus2.pdf"
```

i.e., a new row for each document to be considered inside the request.

