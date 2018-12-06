<?xml version="1.0" encoding="UTF-8"?>
<!--      * cmi2csv *      -->
<!--         2.2.2         -->
<!--   * programmed by *   -->
<!-- * Klaus Rettinghaus * -->
<xsl:stylesheet xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" exclude-result-prefixes="tei">
  <xsl:output encoding="UTF-8" indent="no" method="text"/>
  <xsl:strip-space elements="*"/>
  <!-- define csv seperator -->
  <xsl:param name="dlm" select="','"/>
  <xsl:template match="/">
    <!-- header -->
    <xsl:text>"sender"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"senderID"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"senderPlace"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"senderPlaceID"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"senderDate"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"addressee"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"addresseeID"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"addresseePlace"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"addresseePlaceID"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"addresseeDate"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"edition"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"key"</xsl:text>
    <xsl:value-of select="$sep"/>
    <xsl:text>"note"</xsl:text>
    <xsl:value-of select="'&#10;'"/>
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="tei:fileDesc"/>
  <xsl:template match="tei:profileDesc">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="tei:correspDesc">
    <xsl:apply-templates select="tei:correspAction[@type='sent']"/>
    <xsl:if test="not(tei:correspAction[@type='sent'])">
      <xsl:value-of select="concat($sep,$sep,$sep,$sep)"/>
    </xsl:if>
    <xsl:value-of select="$sep"/>
    <xsl:apply-templates select="tei:correspAction[@type='received']"/>
    <xsl:if test="not(tei:correspAction[@type='received'])">
      <xsl:value-of select="concat($sep,$sep,$sep,$sep)"/>
    </xsl:if>
    <xsl:value-of select="$sep"/>
    <xsl:choose>
      <xsl:when test="@source">
        <xsl:variable name="biblref">
          <xsl:value-of select="substring-after(@source,'#')"/>
        </xsl:variable>
        <xsl:value-of select="concat('&quot;',/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl[@xml:id=$biblref],'&quot;')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="concat('&quot;',normalize-space(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc),'&quot;')"/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:value-of select="$sep"/>
    <xsl:choose>
      <xsl:when test="@key">
        <xsl:value-of select="concat('&quot;',@key,'&quot;')"/>
      </xsl:when>
      <xsl:when test="@ref and not(@key)">
        <xsl:value-of select="@ref"/>
      </xsl:when>
    </xsl:choose>
    <xsl:value-of select="$sep"/>
    <xsl:apply-templates select="tei:note"/>
    <xsl:value-of select="'&#10;'"/>
  </xsl:template>
  <xsl:template match="tei:date">
    <xsl:value-of select="'&quot;'"/>
    <xsl:choose>
      <xsl:when test="@when">
        <xsl:value-of select="@when"/>
        <xsl:if test="@cert or @evidence">
          <xsl:text>?</xsl:text>
        </xsl:if>
      </xsl:when>
      <xsl:when test="@from or @to">
        <xsl:choose>
          <xsl:when test="@cert or @evidence">
            <xsl:value-of select="concat(@from,'?/',@to,'?')"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="concat(@from,'/',@to)"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="@notBefore or @notAfter">
        <xsl:text>[</xsl:text>
        <xsl:if test="@notBefore">
          <xsl:value-of select="@notBefore"/>
        </xsl:if>
        <xsl:text>..</xsl:text>
        <xsl:if test="@notAfter">
          <xsl:value-of select="@notAfter"/>
        </xsl:if>
        <xsl:text>]</xsl:text>
      </xsl:when>
      <xsl:otherwise/>
    </xsl:choose>
    <xsl:value-of select="'&quot;'"/>
  </xsl:template>
  <xsl:template match="tei:note">
    <xsl:value-of select="'&quot;'"/>
    <xsl:value-of select="text()"/>
    <xsl:value-of select="'&quot;'"/>
  </xsl:template>
  <xsl:template match="tei:correspAction">
    <xsl:value-of select="concat('&quot;',normalize-space(tei:persName),'&quot;')"/>
    <xsl:value-of select="$sep"/>
    <xsl:value-of select="concat('&quot;',tei:persName/@ref,'&quot;')"/>
    <xsl:value-of select="$sep"/>
    <xsl:value-of select="concat('&quot;',normalize-space(tei:placeName),'&quot;')"/>
    <xsl:value-of select="$sep"/>
    <xsl:value-of select="concat('&quot;',tei:placeName/@ref,'&quot;')"/>
    <xsl:value-of select="$sep"/>
    <xsl:apply-templates select="tei:date[1]"/>
  </xsl:template>
</xsl:stylesheet>
