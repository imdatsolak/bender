#!/usr/bin/perl
#

# `curl -O http://www.onomastik.com/Vornamen-Lexikon/sprache_2_deutsch.php`;
@malenames = ();
@femalenames = ();
foreach $gender ('m', 'j') {
	foreach $char ('a' .. 'z') {
		$str = sprintf("%s%s-vornamen.htm", $gender, $char);
		$url = "http://www.vornamenlexikon.de/$str";
#		print($url);
#		system("curl -O $url");
		open(INFILE, $str);
		@lines = <INFILE>;
		foreach $line (@lines) {
			chomp($line);
			$line =~ s/\<.*//g;
			$line =~ s/.*\>//g;
			$line =~ s/ //g;
			if ($line !~ /^$/) {
				if ($gender =~ /j/) {
					print("$line\n");
					push(@malenames, $line);
				} else {
					push(@femalenames, $line);
				}
			}
		}
	}
}

open(M, '>male-names.txt');
foreach $l (@malenames) {
	print M "$l\n";
}
close(M);
open(F, ">fem-names.txt");
foreach $l (@femalenames) {
	print F "$l\n";
}
close(F);
