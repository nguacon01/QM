%include( "Head.tpl", title="Done Jobs")
</head>
<body>
<div id="container">
<a href="/QM">Back to home page</a>
<H1>{{name}}</H1>
<hr/>
% if fich:
	<h2>files</h2>
	<ul>
	%for i in fich:
	    <li><a href="/view/QM_dJobs/{{name}}/{{i}}">{{i}}</a></li>
	%end
	</ul>
	<hr/>
%end
%if dire:
	<h2>directories</h2>
	<ul>
	%for i in dire:
	   <li><a href="{{i}}/">{{i}}/</a></li>
	%end
	</ul>
	<hr>
%end

<p><i>determined at {{now}}</i></p>
</div>
</body>
</html>
