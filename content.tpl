<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
    <metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"       xmlns:opf="http://www.idpf.org/2007/opf" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:calibre="http://calibre.kovidgoyal.net/2009/metadata" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{title}</dc:title>
        <dc:creator opf:file-as="{authorformat}" opf:role="aut">{author}</dc:creator>
        <meta name="calibre:title_sort" content="{title}"/>
        <meta name="cover" content="cover"/>
        {extrameta}
    </metadata>
    <manifest>
        {manifest}
    </manifest>
    <spine toc="ncx">
        {spine}
    </spine>
    <guide>
        <reference href="{cover}" type="cover" title="Cover"/>
    </guide>
</package>