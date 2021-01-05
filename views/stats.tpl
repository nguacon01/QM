%include( "Head.tpl", title="Usage Statitics")
</head>
<body>
<div id="container">
<a href="/QM">Back to home page</a>
<H1>Usage Statitics</H1>
<hr/>
<h2>files</h2>
<table CELLPADDING=5>
<tr><th>Owner</th><th>nb of Jobs</th><th>CPU time</th></tr>
%for u in cpu_users.keys():
    <tr>
        <td><b>{{u}}</b></td>
        <td>{{job_users[u]}} jobs</td>
        <td>{{time_users[u]}}</td>
    </tr>
%end
<tr></tr>
<tr><td>Total</td><td>{{jobtotal}} jobs</td><td>{{timetotal}}</td></tr>
</table>
<p>mean job duration : {{meanjob}}
<hr/>

<p><i>determined  {{now}}</i></p>
</div>
</body>
</html>
