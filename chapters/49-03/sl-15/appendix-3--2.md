# APPENDIX 3
NOTAM FORMAT
Message series, number and identifier NOTAM containing new information NOTAMN
... (series and number/year) NOTAM replacing a previous NOTAM NOTAMR ...
... (series and number/year of NOTAM to be replaced) (series and number/year) NOTAM canceling a previous NOTAM NOTAMC ...
... (series and number/year of NOTAM to be cancelled) (series and number/year)
FIR NOTAM Code Traffic Purpose Scope Lower Upper Co-ordinates, Radius
limit limit
Identification of ICAO location indicator in which the facility airspace or condition reported on is located A)
Period of Validity
To (PERM or date-time group) EST*
C) PERM*
Text of NOTAM; Plain-language Entry (using ICAO Abbreviations)
Upper Limit G)
INSTRUCTIONS FOR THE COMPLETION OF
THE NOTAM FORMAT
1. General The qualifier line Item Q and all identifiers Items A to G inclusive each followed by a closing parenthesis, as shown in the format, shall be transmitted unless there is no entry to be made against a particular identifier.
2. NOTAM numbering Each NOTAM shall be allocated a series identified by a letter and a four-digit number followed by a stroke and a two-digit number for the year (e.g., A0023/03. Each series shall start on 1st January with the number 0001).
3. Qualifiers Item Q Item Q is divided in eight fields, each separated by a stroke. An entry shall be made in each field. Examples of how fields are to be filled are shown in the Aeronautical Information Services Manual (Doc 8126). The definition of the field is as follows:
(a) FIR-
(i) where the subject of the information is located
geographically within one FIR, the ICAO location indicator shall be that of the FIR concerned. When an aerodrome is situated within an overlying FIR of another State, the first field of Item (Q) shall contain the code for that overlying FIR; or
(ii) where the subject of the information is located
geographically with more than one FIR, the FIR field shall be composed of the ICAO nationality letters of the State originating the NOTAM followed by "XX". The ICAO location indicators of the FIRs concerned shall then be listed in Item (A) or indicator of the State or non-governmental agency which is responsible for provision of air navigation service in more than one State;
(b) NOTAM CODE-
All NOTAM Code groups contain a total of five letters and the first letter is always the letter Q. The second and third letters identify the subject, and the fourth and fifth letters denote the status or condition of the subject reported upon. The two-letter codes for subjects and conditions are those contained in the PANS-ABC (DOC 8400). For combinations of second and third and fourth and fifth letters, the NOTAM Selection Criteria contained in Doc 8126 or insert one of the following combinations, as appropriate-
(i) if the subject is not listed in the NOTAM Code (Doc 8400)
or in the NOTAM Selection Criteria (Doc 8126), insert "XX" as the second and third letters (e.g., QXXAK);
(ii) if the condition of the subject is not listed in the
NOTAM Code (Doc 8400) or in the NOTAM Selection Criteria (Doc 8126), insert "XX" as the fourth and fifth letters (e.g., QFAXX);
(iii) where a NOTAM containing operationally significant
information is issued in accordance with Appendix 4 and Chapter 6 and when it is used to announce existence of AIRAC AIP Amendments or Supplements, insert "TT" as the fourth and fifth letters of the NOTAM Code;
(iv) where a NOTAM is issued containing a checklist of
valid NOTAM, insert "KKKK" as the second, third, fourth and fifth letters; and
(v) the following fourth and fifth letters of the NOTAM
Code shall be used in NOTAM cancellations:
AK: Resumed normal operation AL: Operative or Re-operative subject to previously
published limitations or conditions
AO: Operational CC: Completed CN: Cancelled
HV: Work completed
XX: Plain language
(c) TRAFFIC
I = IFR V= VFR K= NOTAM is a checklist
Note: Depending on the NOTAM subject and content, the qualifier field TRAFFIC may contain
combined qualifiers. Guidance concerning the combination of TRAFFIC qualifiers with subject and conditions in accordance with the NOTAM Selection Criteria is contained in
(d) PURPOSE
N = NOTAM selected for the immediate attention of
aircraft operators
B = NOTAM selected for PIB entry
O = NOTAM concerning flight operations M= Miscellaneous NOTAM; not subject for a briefing,
but it is available on request
K = NOTAM is a checklist
Note: Depending on the NOTAM subject and content, the qualifier field PURPOSE may contain
combined qualifiers BO of NBO. Guidance concerning the combination of PURPOSE qualifiers with subject and conditions in accordance with the NOTAM Selection Criteria is contained in DOC 8126.
(e) SCOPE
A = Aerodrome E = En route W= Nav Warning K = NOTAM is a checklist
Note: Depending on the NOTAM subject and content, the qualifier field PURPOSE may contain
combined qualifiers BO of NBO. Guidance concerning the combination of PURPOSE qualifiers with subject and conditions in accordance with the NOTAM Selection Criteria is contained in DOC 8126.
(f) LOWER AND UPPER
LOWER and UPPER limits shall only be expressed in flight levels (FL) and shall express the actual vertical limits of the area of influence with the addition of buffers. In the case of navigation warnings and airspace restrictions, values entered shall be consistent with those provided under Items F and G. Where the subject does not contain specific height information, insert "000" for LOWER and "999" for UPPER as default values.
(g) CO-ORDINATES, RADIUS
The latitude and longitude accurate to one minute, as well as a three-digit distance figure giving the radius of influence in NM (e.g., 4700N01140E043). Co-ordinates present approximate centre of circle whose radius encompasses the whole area of influence, and if the NOTAM affects the entire FIR, enter the default value "999" for radius.
4. Item A Insert the location indicator as contained in ICAO Doc 7910 of the aerodrome or FIR in which the facility, airspace, or condition being reported on is located. More than one FIR or IR may be indicated when appropriate. If there is no available ICAO location indicator, use the ICAO nationality letter as given in ICAO Doc 7910, Part 2, plus "XX" and followed up in Item E by the name, in plain language. If information concerns GNSS, insert the appropriate ICAO location indicator allocated for a GNSS element or the common location indicator allocated for all elements of GNSS (except GBAS).
Note: In the case of GNSS, the location indicator may be used when identifying a GNSS element
outage (e.g., KNMH for a GPS satellite outage). 5. Item B For the date-time group, use a ten-figure group, giving year, month, day, hours and minutes in UTC and this entry shall be the date-time at which the NOTAMN, comes into force. in the cases of NOTAMR and NOTAMC, the date-time group is the actual date and time of the NOTAM origination. The start of a day shall be indicated by "0000".
6. Item C With the exception of NOTAMC, a ten-figure day-time group giving year, month, day, hours and minutes in UTC indicating duration of information shall be used unless the information is of a permanent nature in which case the abbreviation "PERM" is inserted instead. The end of the day shall be indicated by "2359" and not "2400". Where the information on timing is uncertain, the approximate duration shall be indicated using a date-time group followed by the abbreviation "EST". Any NOTAM which includes an "EST" shall be cancelled or replaced before the date-time specified in Item C.
7. Item D Where the hazard, status of operation or condition of facilities being reported on will be active in accordance with a specific time and date schedule between the dates-times indicated in Items (B) and (C), insert such information under Item (D). Where Item (D) exceeds two hundred characters, consideration shall be given to providing such information in a separate, consecutive NOTAM.
Note: Guidance concerning a harmonised definition of Item (D) content is provided in
Doc 8126. 8. Item E Use decoded NOTAM Code, complemented where necessary by ICAO abbreviations, indicators, identifiers, designators, call signs, frequencies, figures and plain language. When NOTAM is selected for international distribution, English text shall be included for those parts expressed in plain language. This entry shall be clear and concise in order to provide a suitable PIB entry. In the case of NOTAMC, a subject reference and status message shall be included to enable accurate plausibility checks.
9. Items F and G These items are normally applicable to navigation warnings or airspace restrictions and are usually part of the PIB entry. Insert both lower and upper height limits of activities or restrictions, clearly indicating only one reference datum and units of measurement. The abbreviations GND or SFC shall be used in Item F to designate ground and surface respectively. The abbreviation UNL shall be used in Item G to designate unlimited.
Note: For NOTAM examples see Doc 8126 and the PANS-ABC (Doc 8400).
PART D
AERONAUTICAL INFORMATION, REGULATION
AND CONTROL (AIRAC)
The standards required to be met for AIRAC shall be as follows:
GENERAL SPECIFICATIONS
1. (1) Information concerning the circumstances listed in Part 1 of the Appendix, shall be distributed under AIRAC, basing establishment, withdrawal or significant changes upon a series of common effective dates at intervals of twenty-eight days, including 14th January, 2010.
(2) Information notified in the AIRAC shall not be changed further for at least another twenty-eight days after the effective date, unless the circumstance notified is of a temporary nature and would not persist for the full period.
(3) Where information has not been submitted by the AIRAC date, a NIL notification shall be originated and distributed by NOTAM or other suitable means, not later than one cycle before the AIRAC effective date concerned.
(4) Implementation dates other than the AIRAC effective dates shall not be used for pre-planned operationally significant changes requiring cartographic work or for updating of navigation databases.
PROVISION OF INFORMATION IN PAPER COPY FORM
2. In all circumstances, information provided under the AIRAC system shall be published in paper copy form and distributed by the AIS unit at least forty-two days in advance of the effective date with the objective of reaching recipients at least twenty-eight days in advance of the effective date.
PROVISION OF INFORMATION IN ELECTRONIC FORM
3. (1) Where the Authority has established an aeronautical database in and thereafter updates the contents of that database concerning the circumstances listed in Part 1 of the Appendix, the Authority shall ensure that the effective dates of the data coincide with the established AIRAC effective dates used for the provision of information in paper copy form.
(2) The information provided in electronic form, concerning the circumstances listed in Part 1 of the Appendix, shall be distributed and made available by the AIS unit so as to reach recipients at least twenty-eight days in advance of the AIRAC effective date.
- Margin: Part C. Paragraph 2(1) and (13).
- Margin: Priority indicator
- Margin: Address
- Margin: Date and time of filing Originator's indicator
- Margin: From (date-time group) B)
- Margin: Time Schedule (if applicable) D)
- Margin: E)
- Margin: Lower Limit F)
- Margin: Signature
- Margin: *Delete as appropriate
- Margin: Doc 8126.
- Margin: Regulation 22.
