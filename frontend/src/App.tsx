import React, {useState,  useEffect} from 'react';

function index() {
  const [message, setMessage] = useState("Loading")

  useEffect(() => {
    fetch("http://localhost:8080/home")
      .then(response => response.json())
      .then(data => {
        // Initially, message = "Loading"
        // Then, after it receives the data from server, message = data.message
        setMessage(data.message);
        console.log(data);
      })
      .catch(error => console.error("Error: ", error))
  }, []);

  return (
    <div>{message}</div>
  )
}

export default index;
