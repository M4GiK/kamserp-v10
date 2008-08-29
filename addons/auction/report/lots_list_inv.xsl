<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">

	<xsl:template match="/">
		<xsl:apply-templates select="lots"/>
	</xsl:template>

	<xsl:template match="lots">
		<document xmlns:fo="http://www.w3.org/1999/XSL/Format">
			<template leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm" title="Releve de compte" author="Generated by Tiny ERP, Fabien Pinckaers" allowSplitting="20">
				<pageTemplate id="all">
					<pageGraphics/>
					<frame id="list" x1="1.0cm" y1="2.0cm" width="19.0cm" height="27cm"/>
				</pageTemplate>
			</template>

			<stylesheet>
				<paraStyle name="small" fontName="Courier" fontSize="12" spaceBefore="0mm" spaceAfter="0mm"/>
				<paraStyle name="verysmall" fontSize="10" fontName="Courier" spaceBefore="0mm" spaceAfter="0mm"/>
				<paraStyle name="smallest" fontSize="8" fontName="Courier" spaceBefore="-1mm" spaceAfter="-1Mm"/>

				<blockTableStyle id="left">
					<blockValign value="TOP"/>
					<blockAlignment value="LEFT"/>
					<blockFont name="Helvetica-Bold" size="10"/>
					<blockTextColor colorName="black"/>
					<lineStyle kind="LINEABOVE" thickness="0.5" colorName="black" start="0,0" stop="-1,0"/>
					<lineStyle kind="LINEABOVE" thickness="0.5" colorName="black" start="0,0" stop="-1,0"/>
					<lineStyle kind="LINEBELOW" thickness="0.5" colorName="black"/>
					<lineStyle kind="LINEBEFORE" thickness="0.5" colorName="black" start="0,0" stop="-1,-1"/>
					<lineStyle kind="LINEBEFORE" thickness="0.5" colorName="black" start="0,0" stop="0,-1"/>
					<lineStyle kind="LINEAFTER" thickness="0.5" colorName="black" start="-1,0" stop="-1,-1"/>
					<blockBackground colorName="(1,1,1)" start="0,0" stop="-1,-1"/>
					<blockBackground colorName="(0.88,0.88,0.88)" start="0,0" stop="-1,0"/>
				</blockTableStyle>
			</stylesheet>

			<story>
				<blockTable repeatRows="1" style="left" colWidths="2.4cm,2.2cm,12.0cm,1.8cm">
					<tr>
						<td>
							<para style="small"><b t="1">Inv.</b></para>
						</td><td>
							<para style="small"><b t="1">List N.</b></para>
						</td><td>
							<para style="small"><b t="1">Description</b></para>
						</td><td>
							<para style="small"><b t="1">Cat. N.</b></para>
						</td>
					</tr>
					<xsl:apply-templates select="lot">
						<xsl:sort data-type="number" select="deposit_num"/>
						<xsl:sort data-type="number" select="lot_num"/>
					</xsl:apply-templates>
				</blockTable>
			</story>
		</document>
	</xsl:template>

	<xsl:template match="lot">
		<tr>
			<td>
				<para style="verysmall">
					<xsl:value-of select="deposit_num"/>
				</para>
			</td><td>
				<para style="verysmall">
					<xsl:value-of select="lot_num"/>
				</para>
			</td><td>
				<para style="verysmall">
				    <xsl:value-of select="name"/>
				</para>
				<para style="verysmall">
				    <xsl:value-of select="desc"/>
				</para>
			</td><td>
				<para style="verysmall">
					<xsl:value-of select="obj_num"/>
				</para>
			</td>
		</tr>
	</xsl:template>
</xsl:stylesheet>
