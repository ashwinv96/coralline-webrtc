let localStream;
let remoteStream;
let peerConnection;
let socket;
let makingOffer = false;
let polite = false;
let ignoreOffer = false;

const config = {
  iceServers: [
    { urls: ["stun:stun.l.google.com:19302"] },
  ],
};

let roomName = window.location.pathname.split("/")[2];

const init = async () => {
  // Get media
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  document.getElementById("user-1").srcObject = localStream;

  // Connect WebSocket
  socket = new WebSocket(`wss://${window.location.host}/ws/${roomName}`);

  socket.onopen = async () => {
    await createPeerConnection();
  };

  socket.onmessage = async ({ data }) => {
    data = JSON.parse(data);

    switch (data.type) {
      case "USER_JOIN":
        console.log("Another user joined. I'm polite.");
        polite = true;
        break;

      case "OFFER":
      case "ANSWER":
        await handleDescription(data);
        break;

      case "candidate":
        if (peerConnection && data.candidate) {
          try {
            await peerConnection.addIceCandidate(data.candidate);
          } catch (e) {
            if (!ignoreOffer) throw e;
          }
        }
        break;
    }
  };
};

const createPeerConnection = async () => {
  peerConnection = new RTCPeerConnection(config);
  remoteStream = new MediaStream();
  document.getElementById("user-2").srcObject = remoteStream;

  localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

  peerConnection.ontrack = ({ streams: [stream] }) => {
    stream.getTracks().forEach(track => remoteStream.addTrack(track));
  };

  peerConnection.onicecandidate = ({ candidate }) => {
    if (candidate) {
      socket.send(JSON.stringify({ type: "candidate", candidate }));
    }
  };

  peerConnection.onnegotiationneeded = async () => {
    try {
      makingOffer = true;
      await peerConnection.setLocalDescription();
      socket.send(JSON.stringify({ type: "OFFER", message: peerConnection.localDescription }));
    } catch (err) {
      console.error("Negotiation error:", err);
    } finally {
      makingOffer = false;
    }
  };
};

const handleDescription = async ({ type, message }) => {
  const readyForOffer = !makingOffer && (peerConnection.signalingState === "stable" || peerConnection.signalingState === "have-local-offer");
  const offerCollision = type === "OFFER" && !readyForOffer;

  ignoreOffer = !polite && offerCollision;
  if (ignoreOffer) return;

  try {
    await peerConnection.setRemoteDescription(message);
    if (type === "OFFER") {
      await peerConnection.setLocalDescription(await peerConnection.createAnswer());
      socket.send(JSON.stringify({ type: "ANSWER", message: peerConnection.localDescription }));
    }
  } catch (err) {
    console.error("Error handling description:", err);
  }
};

document.addEventListener("DOMContentLoaded", init);
