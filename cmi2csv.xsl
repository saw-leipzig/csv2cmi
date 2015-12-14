<?xml version="1.0" encoding="UTF-8"?>
<!-- * cmi2csv * -->
<!-- version 1.0 -->
<xsl:stylesheet xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" exclude-result-prefixes="tei">
  <xsl:output encoding="UTF-8" method="text"/>
  <xsl:template match="/">
    <xsl:text>sender,senderID,senderPlace,senderPlaceID,senderDate,addressee,addresseeID,addresseePlace,addresseePlaceID,addresseeDate,edition,key
    </xsl:text>
    <xsl:for-each select="//tei:correspDesc">
      <xsl:text>"</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='sent']/tei:persName"/>
      <xsl:text>",</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='sent']/tei:persName/@ref"/>
      <xsl:text>,"</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='sent']/tei:placeName"/>
      <xsl:text>",</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='sent']/tei:placeName/@ref"/>
      <xsl:text>,</xsl:text>
      <xsl:if test="tei:correspAction[@type='sent']/tei:date/@cert">
        <xsl:text>[</xsl:text>
      </xsl:if>
      <xsl:value-of select="tei:correspAction[@type='sent']/tei:date/@when"/>
      <xsl:if test="tei:correspAction[@type='sent']/tei:date/@cert">
        <xsl:text>]</xsl:text>
      </xsl:if>
      <xsl:text>,"</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='received']/tei:persName"/>
      <xsl:text>",</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='received']/tei:persName/@ref"/>
      <xsl:text>,"</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='received']/tei:placeName"/>
      <xsl:text>",</xsl:text>
      <xsl:value-of select="tei:correspAction[@type='received']/tei:placeName/@ref"/>
      <xsl:text>,</xsl:text>
      <xsl:if test="tei:correspAction[@type='received']/tei:date/@cert">
        <xsl:text>[</xsl:text>
      </xsl:if>
      <xsl:value-of select="tei:correspAction[@type='received']/tei:date/@when"/>
      <xsl:if test="tei:correspAction[@type='received']/tei:date/@cert">
        <xsl:text>]</xsl:text>
      </xsl:if>
      <xsl:text>,"</xsl:text>
      <xsl:variable name="biblref">
        <xsl:value-of select="substring-after(@source,'#')"/>
      </xsl:variable>
      <xsl:value-of select="/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl[@xml:id=$biblref]"/>
      <xsl:text>",</xsl:text>
      <xsl:value-of select="@key"/>
      <xsl:text>
      </xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
