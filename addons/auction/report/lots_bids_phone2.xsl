<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">
	<xsl:import href="../../custom/corporate_defaults.xsl"/>

	<xsl:template match="/">
		<xsl:apply-templates select="lots"/>
	</xsl:template>

	<xsl:template match="/">
		<document xmlns:fo="http://www.w3.org/1999/XSL/Format">
			<template leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm" title="Releve de compte" author="Generated by Tiny ERP, Fabien Pinckaers" allowSplitting="20" pageSize="(21cm,29.7cm)">

				<pageTemplate id="all">
					<frame id="list" x1="1.0cm" y1="1.0cm" height="22.7cm" width="19cm"/>

					<pageGraphics>
					<xsl:apply-imports/>
					</pageGraphics>
				</pageTemplate>
			</template>

			<stylesheet>
				<paraStyle name="small" fontName="Courier" fontSize="12" spaceBefore="0mm" spaceAfter="0mm"/>
				<paraStyle name="verysmall" fontSize="11" fontName="Courier" spaceBefore="0mm" spaceAfter="0mm"/>
				<paraStyle name="smallest" fontSize="10" fontName="Courier" spaceBefore="-0.5mm" spaceAfter="-0.5mm"/>

				<blockTableStyle id="left">
					<blockValign value="TOP"/>
					<blockAlignment value="LEFT"/>
					<blockFont name="Helvetica-Bold" size="10"/>
					<blockTextColor colorName="black"/>
					<lineStyle kind="LINEABOVE" thickness="0.5" colorName="black" start="0,0" stop="-1,0"/>
					<lineStyle kind="LINEBELOW" thickness="0.5" colorName="black"/>
					<blockBackground colorName="(1,1,1)" start="0,0" stop="-1,-1"/>
					<blockBackground colorName="(0.88,0.88,0.88)" start="0,0" stop="-1,0"/>
				</blockTableStyle>

				<blockTableStyle id="lots">
					<lineStyle kind="LINEABOVE" thickness="0.5" colorName="black" start="0,0" stop="-1,0"/>
					<lineStyle kind="LINEBELOW" thickness="0.5" colorName="black" start="0,-1" stop="-1,-1"/>
				</blockTableStyle>
			</stylesheet>

			<story>
				<blockTable repeatRows="1" style="left" colWidths="1.8cm,10.0cm,1.8cm,4.4cm">
					<tr>
						<td>
							<para style="small"><b t="1">Obj.</b></para>
						</td><td>
							<para style="small"><b t="1">Name</b></para>
						</td><td>
							<para style="small"><b t="1">Bid</b></para>
						</td><td>
							<para style="small"><b t="1">Phone</b></para>
						</td>
					</tr>
				</blockTable>
				<xsl:apply-templates select="lots/lot"/>
			</story>
		</document>
	</xsl:template>

	<xsl:template match="lots/lot[count(bid[tocall='1'])>0]">
		<xsl:variable name="number" select="number"/>
		<blockTable colWidths="1.8cm,10.0cm,1.8cm,4.4cm" style="lots">
			<xsl:for-each select="bid[tocall='1']">
				<tr>
					<td>
						<para style="verysmall"><xsl:value-of select="$number"/></para>
					</td>
					<td>
						<para style="small"><xsl:value-of select="name"/></para>
					</td><td>
						<xsl:value-of select="id"/>
					</td><td>
						<para><b><xsl:value-of select="contact"/></b></para>
					</td>
				</tr>
			</xsl:for-each>
		</blockTable>
	</xsl:template>

</xsl:stylesheet>
