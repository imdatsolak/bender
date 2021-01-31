# CSV Converter

This directory contains the tool required to convert CSV-files into final training format.

The CSV-files MUST BE delimited by TAB.

Following Column-Titles can be used:
- Category - MANDATORY - Number (1...)
- Type: MANDATORY, one of 'B','M', or 'E':
	- B: Initial response, containing a question (for conversations)
	- M: Middle-response, containing possibly another questions
	- E: End-(Final)-Response. Note: most of the responses will be 'E'
- Question: MANDATORY
- Answer: MANDATORY
- A-M<n>-C<n>-UG<n>: OPTIONAL
	- Answer for Client (M) number 'n'
	- ... Channel (C) number 'n'
	- ... UserGroup (UG) number 'n'

Note: If you have Client/Channel/UG-Specific answer for ONE question, you must have such answers for ALL questions.

Also, the file MUST be in UTF-8 encoding!
