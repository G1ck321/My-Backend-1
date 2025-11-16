import { useEffect } from "react";
import React, {useState} from "react";

function Clock(props) {
    
    const [currentTime, setCurrentTime] = useState(new Date());
    setInterval(()=>setCurrentTime(new Date()),1000);
    return(
    <>
    <div id="time"><p>The time is { currentTime.toString()}</p></div>
    </>
    );
}
export default Clock;