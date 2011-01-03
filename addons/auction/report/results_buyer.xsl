<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">

<xsl:variable name="number_columns">2</xsl:variable>

<xsl:variable name="initial_left_pos">1.2</xsl:variable>
<xsl:variable name="width_increment">9.5</xsl:variable>
<xsl:variable name="frame_width">9.0cm</xsl:variable>

<xsl:variable name="width_col1">1.2cm</xsl:variable>
<xsl:variable name="width_col2">1.8cm</xsl:variable>
<xsl:variable name="width_col3">6cm</xsl:variable>

<xsl:variable name="bottom_pos">2.4cm</xsl:variable>
<xsl:variable name="frame_height">26cm</xsl:variable>

<xsl:template match="/">
	<xsl:apply-templates select="results"/>
</xsl:template>

<xsl:template match="results">
	<document filename="example_5.pdf">
	<template pageSize="21cm,29.7cm" leftMargin="1.5cm" rightMargin="1.5cm" topMargin="1.5cm" bottomMargin="1.5cm" title="Bordereau acheteur" author="Generated by Open ERP, Fabien Pinckaers" allowSplitting="20">
		<pageTemplate id="main">
			<pageGraphics>
				<fill color="(0.4,0.4,0.4)"/>
				<stroke color="(0.4,0.4,0.4)"/>
				<setFont name="Helvetica" size="8"/>
				<drawString x="1.8cm" y="1.4cm"><xsl:value-of select="auction/name"/></drawString>
				<drawRightString x="19.2cm" y="1.4cm"><xsl:value-of select="auction/date-au1"/></drawRightString>
				<lineMode width="0.2mm"/>
				<lines>1.8cm 1.8cm 19.2cm 1.8cm</lines>
			</pageGraphics>
			<xsl:apply-templates select="lines/lot" mode="frames"/>
		</pageTemplate>
	</template>

	<stylesheet>
		<paraStyle name="name" fontName="Helvetica-Bold" fontSize="16" alignment="center"/>
		<blockTableStyle id="result">
			 <blockValign value="TOP"/>
			 <blockAlignment value="CENTER" start="0,0" stop="-1,0"/>
			 <blockAlignment value="RIGHT" start="0,1" stop="-1,-1"/>
			 <blockFont name="Helvetica-BoldOblique" size="12" start="0,0" stop="-1,0"/>
			 <blockBackground colorName="grey" start="0,0" stop="-1,0"/>
			 <blockTextColor colorName="white" start="0,0" stop="-1,0"/>
			 <lineStyle kind="LINEBELOW" colorName="red" start="0,0" stop="-1,0"/>
			 <lineStyle kind="LINEBEFORE" colorName="grey" start="-2,0" stop="-2,-1"/>
			 <lineStyle kind="LINEBEFORE" colorName="grey" start="-1,0" stop="-1,-1"/>
			 <lineStyle kind="LINEBEFORE" colorName="black" start="0,1" stop="0,-1"/>
			 <lineStyle kind="LINEAFTER" colorName="black" start="-1,1" stop="-1,-1"/>
		</blockTableStyle>
	</stylesheet>
	
	<story>
		<xsl:apply-templates select="lines"/>
	</story>
	
	</document>
</xsl:template>

<xsl:template match="lines/lot" mode="frames">
	<xsl:if test="position() &lt; $number_columns + 1">
		<frame>
			<xsl:attribute name="width">
				<xsl:value-of select="$frame_width"/>
			</xsl:attribute>
			<xsl:attribute name="height">
				<xsl:value-of select="$frame_height"/>
			</xsl:attribute>
			<xsl:attribute name="x1">
				<xsl:value-of select="$initial_left_pos + (position()-1) * $width_increment"/>
				<xsl:text>cm</xsl:text>
			</xsl:attribute>
			<xsl:attribute name="y1">
				<xsl:value-of select="$bottom_pos"/>
			</xsl:attribute>
		</frame>
	</xsl:if>
</xsl:template>

<xsl:template match="lines">
	<blockTable  repeatRows="1" style="result">
		<xsl:attribute name="colWidths">
			<xsl:value-of select="$width_col1"/>
			<xsl:text>, </xsl:text>
			<xsl:value-of select="$width_col2"/>
			<xsl:text>, </xsl:text>
			<xsl:value-of select="$width_col3"/>
		</xsl:attribute>
			
		<tr>
			<td t="1">Num.</td>
			<td t="1">Adj.</td>
			<td t="1">Buyer</td>
		</tr>
		<xsl:apply-templates select="lot" mode="story"/>
	</blockTable>
	<pageBreak/>
</xsl:template>

<xsl:template match="lot" mode="story">
	<tr>
		<td>
			<xsl:value-of select="lot-number"/>
		</td>
		<td>
			<xsl:if test="lot-price!=''">
				<xsl:value-of select="round(lot-price)"/>
			</xsl:if>
		</td>
		<td>
			<para><xsl:value-of select="lot-buyer"/></para>
		</td>
	</tr>
</xsl:template>

</xsl:stylesheet>
