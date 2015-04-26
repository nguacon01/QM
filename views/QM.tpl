%include Head title="QM Jobs Monitor"
<script type="text/JavaScript">
<!--
function timedRefresh(timeoutPeriod) {    setTimeout("location.reload(true);",timeoutPeriod);    }
//   -->
</script>
</head>
<body onload="JavaScript:timedRefresh(30000);" style= "background: url('/static/img/BigReichenbach_Turner.jpg') repeat-y;  background-size: cover;" >
<p><i>determined at {{now}}</i> - <em>This page will refresh automatically every 30 seconds.</em></p>

<H1 style="color:#ffffff">Monitoring QM server</H1>
<div id="container">
<hr>
<h2>Queuing Jobs</h2>

%if waiting:
        <table CELLPADDING=5>
        <tr><th>Name</th><th>Action</th><th>Size</th><th>Owner</th></tr>
        %for i in waiting:
            <tr>
                <td><b>{{i.name}}</b></td>
                <td> <center>
                    <a href="/QM_qJobs/{{i.name}}/">view</a>
                    <a href="/delete/QM_qJobs/{{i.name}}">delete</a>
                </center></td>
                <td>{{i.size}} columns</td>
                <td>{{i.E_mail}}</td>
                <td>{{i.nicedate}}</td>
            </tr>
        %end
        </table>
%else:
        <P>None</p>
%end
</td>
<hr>
<h2>Running Job</h2>
<td>
%if running:
        <table CELLPADDING=5>
        <tr><th>Name</th><th>Progress</th>
            %if licence_to_kill:
                <th>Action</th>
            %end
            <th>Size</th><th>Owner</th></tr>
        <tr><td><b>{{running.name}}</b></td>
        <td><div style="background-color:#EEE; width:100px;"><div style="background-color:#0E0; width:{{running.avancement()}}px;">&nbsp;</div></div></td>
        %if licence_to_kill:
            <td><a href="/kill/{{running.name}}">KILL</a></td>
        %end
        <td>{{running.size}} columns</td>
        <td>{{running.E_mail}}</td>
        <td>Started at :{{running.started}}</td>
        </tr>
        </table>
%else:
        <p>None</p>
%end
</td>
<hr>
<h2>Done Jobs</h2>

<table CELLPADDING=5>
<tr><th>Name</th><th>zip file</th><th>Action</th><th>Duration</th><th>Size</th><th>Owner</th><th>Date</th></tr>

%for i in done:
    <tr>
        <td><b>{{i.name}}</b></td>
        <td> <a href="/download/{{i.name}}">download</a></td>
        <td> <center>
            <a href="/QM_dJobs/{{i.name}}/">view</a>
            <a href="/delete/QM_dJobs/{{i.name}}">delete</a>
        </center></td>
        <td>{{i.time()}} seconds</td>
        <td>{{i.size}} columns</td>
        <td>{{i.E_mail}}</td>
        <td>{{i.nicedate}}</td>
    </tr>
%end
</table>
</td>
<hr>
</div>
</body>
</html>
