"use client";

import { useStream } from "@langchain/langgraph-sdk/react";

import "./App.css";
import ReactMarkdown from 'react-markdown';
import { useEffect, useState } from "react";


{/* <ReactMarkdown>{report}</ReactMarkdown> */}


export default function App() {
  const [partialResponse ,setPartialResponse] =useState("")
    const [finalMessages, setFinalMessages] = useState([]);
    const [user,setUser] = useState("")
//   useEffect(() => {
// console.log(partialResponse)
// }, [partialResponse]);

//  console.log('refreshed')
  const thread = useStream({
    // apiUrl: "http://127.0.0.1:9090",
    apiUrl: "http://127.0.0.1:9999",
    assistantId: "agent",
    // messagesKey: "messages",
    messagesKey: "draft",
    onFinish:(finalevent)=>{
      setPartialResponse("")
      // setFinalMessages(thread.messages); 
      // console.log(finalevent.values.draft)
      // console.log(finalevent.values.messages)
      setFinalMessages(finalevent.values.messages); 
      ; // clear partial
      setUser("")
      },
      
    onCustomEvent: (event, options) => {
      // console.log(event,options)
       setPartialResponse(event)},    //for custom data stream by get_stream_writer
    onError:(e)=>{console.log(e)},
    // onCustomEvent: for custom event handler

  });

// useEffect(()=>{thread.events.forEach(element => {
  
// });((e)=>{console.log(e)})})

  return (
    <div className="chat-container">
 <div className="messages">


       

        {finalMessages.map((msg) => ( 

          <div
            key={msg.id}
            className={`message ${msg.type==="human"? "user": "bot"}`}
          >
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        ))}


        {/* //user message temp. until receive final state  */}
        {user && ( <div className="message user">
            <ReactMarkdown>{user}</ReactMarkdown>
          </div>)}


        {/* Live-streaming partial output */}
        {partialResponse && (
          <div className="message bot">
            <ReactMarkdown>{partialResponse}</ReactMarkdown>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form
        className="input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.target;
          const message = new FormData(form).get("message");
          form.reset();
          setUser(message)
          

          thread.submit({
          // task: message,          
          // revision_number: 1,
          // max_revisions: 2,
          messages:[message]
          },{streamMode:["custom"]});

        }}
      >
       

        {/* Input */}
        <input
          type="text"
          name="message"
          placeholder="Ask a question..."
          autoComplete="off"
        />

        {/* Send/Stop Button */}
        {thread.isLoading ? (
          <button type="button" onClick={() => thread.stop()}>
            Stop
          </button>
        ) : (
          <button type="submit">Send</button>
        )}
      </form>
    </div>
  );
}
