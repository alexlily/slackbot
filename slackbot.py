import os
import time
from slackclient import SlackClient
import random


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"

START_TRIVIA = "trivia"
ADD_QUESTION = "add"
HELP = "help"
questions_filename = 'test.txt'

class TriviaBot():

    def __init__(self):
        self.addingResponse = False
        self.answeringQuestion = False
        self.currentQuestion = -1
        self.questions = []
        self.answers = {}

    def getQuestionList(self):
        with open(questions_filename, "r") as f:
            line = f.readline()
            i = 0
            while line:
                self.questions.append(line)
                self.answers[i] = f.readline()
                line = f.readline()
                i += 1

    def writeQuestion(self, question, answer):
        with open(questions_filename, "a+") as f:
            f.write('\n'+question.encode('utf8'))
            f.write('\n'+answer.encode('utf8'))

    def getState(self):
        print("addingResponse = " ,self.addingResponse , " answeringQuestion = " ,self.answeringQuestion , "currentQuestion " , self.currentQuestion ," questions " , self.questions , "answers " , self.answers)
        return """

        Here's how to play the game:\n
        \n*trivia* command will make triviabot ask you a question. enter the response, and triviabot will tell you if you were right or not
        \n*add* command will let you add a question to its collection. give the question, and then when prompted, give the response.
        \ne.g., "@triviabot add how do I make a new question?" triviabot will acknowledge that you are making a question and prompt for a response, then "@triviabot this is how!"
        \n*help* command will show this message
        """
    def getTriviaQuestion(self):
        if len(self.questions) == 0:
            return "I don't have any questions for you. Add some with the *add* command!"
        self.answeringQuestion = True
        self.currentQuestion = random.randint(0, len(self.questions) - 1)
        return self.questions[self.currentQuestion]

    def handle_command(self, command, channel):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """ 
        response = "Default response"           
        print("handling command " + '\"' + command + '\"')
        if self.addingResponse:
            self.answers[len(self.questions)-1] = command # the last question added is associated with this answer
            self.addingResponse = False
            response = "Ok, the answer to " + self.questions[-1] + " is " + command
            self.writeQuestion(self.questions[-1], command)
        elif self.answeringQuestion:
            print(self.currentQuestion)
            response = "If you answered " + self.answers[self.currentQuestion] + " then you're right! good job!"
            self.answeringQuestion = False
        else:
            if command.startswith(START_TRIVIA):
                response = self.getTriviaQuestion()
            elif command.startswith(ADD_QUESTION):
                question = command[len(ADD_QUESTION)+1:]
                self.questions.append(question)
                self.addingResponse = True
                response = "ok! added " + question + "\nNow add a response"
            elif command.startswith(HELP):
                response = self.getState()
        
        
        slack_client.api_call("chat.postMessage", channel=channel,
                              text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip(), \
                       output['channel']
    return None, None


# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
if slack_client.rtm_connect():
    print("TriviaBot connected and running!")
    triviabot = TriviaBot()
    triviabot.getQuestionList()
    while True:
        command, channel = parse_slack_output(slack_client.rtm_read())
        if command and channel:
            triviabot.handle_command(command, channel)
        time.sleep(READ_WEBSOCKET_DELAY)
else:
    print("Connection failed. Invalid Slack token or bot ID?")
