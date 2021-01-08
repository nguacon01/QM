%include( "Head.tpl", title="Confirm Deletion")
</head>
<body>
    
%if not conf:
    <h1>Please Confirm</h1>
%end
<div id="container">
<center>
%if conf:
    %if queue == "QM_Jobs":
        <h2> {{fil}} KILLED</h2>
        <p><em>Please wait for some time for this action to be displayed</em></p> 
    %else:
        <h2> {{fil}} DELETED</h2>
    %end
    <a href="/QM/">Return</a>
%else:
    <h2>Please confirm deletion of Job {{fil}} ?</h2>
    %if queue == "QM_dJobs":
        <h3>in Done Jobs queue</h3>
        <a href="/delete/{{queue}}/{{fil}}?conf=True">DELETE</a>
    %elif queue == "QM_Jobs":
        <h3>in Running Jobs</h3>
        <a href="/kill/{{fil}}?conf=True">KILL</a>
    %elif queue == "QM_qJobs":
        <h3>in Queueing Jobs</h3>
        <a href="/delete/{{queue}}/{{fil}}?conf=True">DELETE</a>
    %end
    &nbsp; &nbsp; 
    <a href="/QM/">Return</a>
%end
</center>
</div>
</body>
</html>
