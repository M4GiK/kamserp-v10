<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fo="http://www.w3.org/1999/XSL/Format">

    <xsl:import href="hr_custom_default.xsl"/>
    <xsl:import href="hr_custom_rml.xsl"/>

	<xsl:template match="/">
        <xsl:call-template name="rml" />
    </xsl:template>


    <xsl:template name="stylesheet">
		<document filename="timesheet.pdf">
			<template pageSize="29.7cm,21cm" leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm" title="Timesheets" author="Generated by Open ERP, Fabien Pinckaers" allowSplitting="20">
				<pageTemplate id="first">
					<pageGraphics>
						<drawRightString x="19.0cm" y="26.0cm"><xsl:value-of select="date"/></drawRightString>
					</pageGraphics>
					<frame id="col1" x1="2.0cm" y1="2.5cm" width="22.7cm" height="18cm"/>
				</pageTemplate>
			</template>
			
			<stylesheet>
			   <paraStyle name="title" fontName="Helvetica-Bold" fontSize="15.0" leading="17" alignment="CENTER" spaceBefore="12.0" spaceAfter="6.0"/>
		       <blockTableStyle id="week">
		           <blockFont name="Helvetica-BoldOblique" size="12" start="0,0" stop="-1,0"/>
		           <blockBackground colorName="grey" start="0,0" stop="-1,0"/>
		           <blockTextColor colorName="red" start="-1,0" stop="-1,-1"/>
		           <lineStyle kind="LINEBEFORE" colorName="grey" start="-1,0" stop="-1,-1"/>
		           <blockValign value="TOP"/>
		       </blockTableStyle>
			</stylesheet>

			<story>
				<xsl:call-template name="story"/>
			</story>
		</document>
    </xsl:template>

    <xsl:template name="story">
        <spacer length="1cm" />
        <xsl:apply-templates select="report/title"/>
        <spacer length="1cm" />
        <xsl:apply-templates select="report/user"/>
    </xsl:template>

    <xsl:template match="title">
        <para style="title">
            <xsl:value-of select="."/>
        </para>
        <spacer length="1cm"/>
    </xsl:template>

    <xsl:template match="user">
        <para>
            <b>Name:</b>
            <i><xsl:value-of select="name" /></i>
        </para>
        <blockTable colWidths="4cm,1.5cm,1.5cm,1.5cm,1.5cm,1.5cm,1.5cm,1.5cm,1.5cm" style="week">
            <tr>
                <td></td>
                <td>Mon</td>
                <td>Tue</td>
                <td>Wed</td>
                <td>Thu</td>
                <td>Fri</td>
                <td>Sat</td>
                <td>Sun</td>
                <td>Tot</td>
            </tr>
            <xsl:for-each select="week">
                <tr></tr>
                <tr>
                    <td>Week:</td>
                    <td></td>
                    <td>from <xsl:value-of select="weekstart" /> to <xsl:value-of select="weekend" /></td>
                </tr>
                <tr>
                    <td>Worked hours</td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Monday/workhours">
                                <xsl:value-of select="Monday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Tuesday/workhours">
                                <xsl:value-of select="Tuesday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Wednesday/workhours">
                                <xsl:value-of select="Wednesday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Thursday/workhours">
                                <xsl:value-of select="Thursday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Friday/workhours">
                                <xsl:value-of select="Friday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Saturday/workhours">
                                <xsl:value-of select="Saturday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:choose>
                            <xsl:when test="Sunday/workhours">
                                <xsl:value-of select="Sunday/workhours" />
                            </xsl:when>
                            <xsl:otherwise>0</xsl:otherwise>
                        </xsl:choose>							
                    </td>
                    <td>
                        <xsl:value-of select="total/worked" />
                    </td>
                </tr>
            </xsl:for-each>
        </blockTable>
    </xsl:template>
</xsl:stylesheet>
