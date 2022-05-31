# project: p3
# submitter: jsong99
# partner: None

import pandas as pd
from flask import Flask, request, jsonify
import re
#global counts dictionary 
counts = {'a':0,'b':0}

def count_me(fn):
    counts[fn.__name__] = 0
    def wrapper():
        counts[fn.__name__] += 1
        return fn()

    wrapper.__name__ = fn.__name__
    return wrapper

app = Flask(__name__)

@app.route('/')
@count_me
def home():
    index = """
    <html>
       <head>
        <script src="https://code.jquery.com/jquery-3.4.1.js"></script>
        <script>
          function subscribe() {
            var email = prompt("What is your email?", "????");

            $.post({
              type: "POST",
              url: "email",
              data: email,
              contentType: "application/text; charset=utf-8",
              dataType: "json"
            }).done(function(data) {
              alert(data);
            }).fail(function(data) {
              alert("POST failed");
            });
          }
        </script>
      </head>
      <body>
        <h1>Welcome!</h1>
          <p>This site hosts University/College out-of-state tuition dataset. You can browse the data <a href ="browse.html"> here.</a></p>
          <p>Or, if you want to write code to pull the data in JSON form, read about <a href ="api.html">our API</a>.</p>
          <p>To receive updates on college/university tuition is added to the dataset, please subscribe:</p>
          <button onclick="subscribe()">Subscribe</button>
          <p>Of course, hosting this site is terribly expensive, so please...</p>
          """
    version1 =      """
          <h2><a href="donate.html?from=a" style="color:red">Donate</a></h2>
          """
    version2 =      """
          <h2><a href="donate.html?from=b" style="color:blue">Donate</a></h2>
          """

    if counts['home'] <= 10:
        if counts['home'] % 2 is 0:
            index += version1
        else:
            index += version2
    else:
        if counts['a'] == 0 and counts['b'] == 0:
            index += version1
        else:
            if counts['a'] >= counts['b']:
                index += version1
            else:
                index += version2
    end = """
      </body>
    </html>
    """   
    index += end
    
    return index

@app.route('/browse.html')
def browse_handler():
    
    columns=['Name','Private','F.Undergrad','P.Undergrad','Outstate','Books','Personal']
    df = pd.read_csv('main.csv',names = columns)
    df = df.iloc[1:]
    
    page = """
    <html>
    <h1>Browse</h1>
    """
    page += df.to_html()
    page += "</html>"
    return page

@app.route('/api.html')
def api_handler():
    page = """
    <html>
        <h1>API</h1>
        <body>
            <p>To search for a specific school, do this</p>
            <pre>
                /tuition.json?Name=University of Wisconsin at Madison
            </pre>
            <p>To get all tuition, do this </p>
            <pre>
                /tuition.json
            </pre>
            <p>To get all private colleges, do this </p>
            <pre>
                /tuition.json?Private=Yes
            </pre>
        </body>
    </html>
    """
    return page

@app.route('/donate.html')
def donation_handler():
    if len(request.args) is not 0:
        if request.args['from'] == 'a':
            if 'a' in counts.keys():
                counts['a'] += 1
            else:
                counts['a'] = 1
        if request.args['from'] == 'b':
            if 'b' in counts.keys():
                counts['b'] += 1
            else:
                counts['b'] = 1
    page = """
            <html>
                <body>
                    <h1>Donate</h1>
                    <p>please give us your money</p>

                </body>
            </html>
            """
    return page



@app.route('/email', methods=["POST"])
def email():
    email = str(request.data, "utf-8")
    if re.match(r"^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$", email):
        with open("emails.txt", "a") as f: # open file in append mode
            f.write(email + "\n")
        return jsonify("thank you!")
    return jsonify('wrong email format, please enter your email address correctly')
    
@app.route('/tuition.json')
def json_handler():
    columns=['Name','Private','F.Undergrad','P.Undergrad','Outstate','Books','Personal']
    df = pd.read_csv('main.csv',names = columns)
    dataset = df.to_dict('records')
    dataset = dataset[1:]
    result = []
    if len(request.args) != 0:
        for key in request.args:
            for data in dataset:
                if data[key] == request.args[key]:
                    result += [data]
        if len(result) == 1:
            return jsonify(result[0])
        return jsonify(result)
    else:
        return jsonify(dataset)

if __name__ == '__main__':
    app.run(host="0.0.0.0") # don't change this line!