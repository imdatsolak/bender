# Mail Converter

This directory contains the tool and data required to convert mails from .eml (mbox)-format into JSON.

Basically, this tools tries to identifiy the initial conversation within an email, and converts the section of *only* the initial conversation (user -> company -> user) into a JSON-file.

While converting, the email is also (as much as possible) anonymized. Any names or such found are either removed or replaced with the term `__ANONYM__`

The tool uses a firstnames- and a lastnames-database that resides in the `res`-folder. This folder *must* be in the same folder as where you start the tool in.

## Usage

````bash
python convert_mails.py -i <indirectory> -o <outdirectory>
````

The `indirectory` contains mails in the .eml (mbox)-format. One file per email.

The `outdirectory` is where the converted mails are stored.

The tool only converts mails where the *initial* conversation was started by the user, not company. If it cannot find an initial conversation started by a user, it will not convert that email.

Thus, the resulting file-list may be smaller than the original file-list.

## Customization

If you need to use this tool to convert a list of emails, please first edit the lines beginning with:

- `OWN_DOMAINS=`
- `DEFAULT_US=`

You need to provide the own-domains (i.e., the domains from which the *company* sends emails) and provide a 'default_us' (i.e., what should be the default company-email-address.)

Also, if you want to adapt it to any other languge, you need to change the lines:

- `separators=`
- `stupid_sep=`
- `stupid_sep2=`
- `name_lines=`
- `end_of_mail_lines=`
- `ignore_lines=`
- `header_keys=`

Have fun :-)

