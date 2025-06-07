// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

contract MeetingContract {
    struct Meeting {
        uint256 meetingId;
        string title;
        string organizer;
        uint256 startTime;
        uint256 endTime;
        string[] participants;
        bool isActive;
    }

    struct Message {
        string userName;
        string text;
        uint256 timestamp;
    }

    mapping(uint256 => Meeting) private meetings;
    mapping(uint256 => Message[]) private meetingMessages;
    uint256 public meetingCount;

    event MeetingCreated(uint256 indexed meetingId, string title, string organizer);
    event MeetingStarted(uint256 indexed meetingId, uint256 startTime, string[] participants);
    event MessageStored(uint256 indexed meetingId, string userName, string text, uint256 timestamp);
    event MeetingEnded(uint256 indexed meetingId, uint256 endTime);

    // Create a new meeting
    function createMeeting(string memory _title, string memory _organizer) public {
        meetingCount++;
        meetings[meetingCount] = Meeting({
            meetingId: meetingCount,
            title: _title,
            organizer: _organizer,
            startTime: 0,
            endTime: 0,
            participants: new string [](0),
            isActive: false
        });

        emit MeetingCreated(meetingCount, _title, _organizer);
    }

    // Start the meeting with initial participants
    function startMeeting(uint256 _meetingId, uint256 _startTime, string[] memory _participants) public {
        require(meetings[_meetingId].meetingId != 0, "Meeting does not exist");
        require(!meetings[_meetingId].isActive, "Meeting already started");

        meetings[_meetingId].startTime = _startTime;
        meetings[_meetingId].participants = _participants;
        meetings[_meetingId].isActive = true;

        emit MeetingStarted(_meetingId, _startTime, _participants);
    }

    // Store messages along with speaker tracking
    function storeMessage(uint256 _meetingId, string memory _userName, string memory _text) public {
        require(meetings[_meetingId].isActive, "Meeting is not active");

        bool exists = false;
        for (uint256 i = 0; i < meetings[_meetingId].participants.length; i++) {
            if (keccak256(abi.encodePacked(meetings[_meetingId].participants[i])) == keccak256(abi.encodePacked(_userName))) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            meetings[_meetingId].participants.push(_userName);
        }

        meetingMessages[_meetingId].push(Message(_userName, _text, block.timestamp));
        emit MessageStored(_meetingId, _userName, _text, block.timestamp);
    }

    function storeMessagesBatch(
    uint256 _meetingId,
    string[] memory _userNames,
    string[] memory _texts
) public {
    require(meetings[_meetingId].isActive, "Meeting is not active");

    for (uint256 i = 0; i < _userNames.length; i++) {
        string memory userName = _userNames[i];
        string memory text = _texts[i];

        bool exists = false;
        for (uint256 j = 0; j < meetings[_meetingId].participants.length; j++) {
            if (keccak256(abi.encodePacked(meetings[_meetingId].participants[j])) == keccak256(abi.encodePacked(userName))) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            meetings[_meetingId].participants.push(userName);
        }

        meetingMessages[_meetingId].push(Message(userName, text, block.timestamp));
        emit MessageStored(_meetingId, userName, text, block.timestamp);
    }
}


    // End the meeting
    function endMeeting(uint256 _meetingId, uint256 _endTime) public {
        require(meetings[_meetingId].isActive, "Meeting is not active or already ended");

        meetings[_meetingId].endTime = _endTime;
        meetings[_meetingId].isActive = false;

        emit MeetingEnded(_meetingId, _endTime);
    }

    // Retrieve meeting details
    function getMeeting(uint256 _meetingId) public view returns (Meeting memory) {
        return meetings[_meetingId];
    }

    // Retrieve messages for a meeting
    function getMessages(uint256 _meetingId) public view returns (Message[] memory) {
        return meetingMessages[_meetingId];
    }

    // Retrieve participants of a meeting
    function getParticipants(uint256 _meetingId) public view returns (string[] memory) {
        return meetings[_meetingId].participants;
    }

    // Retrieve all meetings
    function getAllMeetings() public view returns (Meeting[] memory) {
        Meeting[] memory allMeetings = new Meeting[](meetingCount);
        for (uint256 i = 1; i <= meetingCount; i++) {
            allMeetings[i - 1] = meetings[i];
        }
        return allMeetings;
    }
}
