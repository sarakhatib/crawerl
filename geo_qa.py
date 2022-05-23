import lxml.html
import rdflib
import requests
import sys
import urllib
from urllib import parse

g = rdflib.Graph()
prefix = "http://en.wikipedia.org"
prefix_for_ontology = "http://example.org/"
first_url = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"

countries_url_dict = dict()
people_url_dict = dict()
visited = set()


def concat_prefix_to_entity_or_property(name):
    return f"{prefix_for_ontology}{name}"


president_of = rdflib.URIRef(concat_prefix_to_entity_or_property("president_of"))
population_of = rdflib.URIRef(concat_prefix_to_entity_or_property("population_of"))
born_in = rdflib.URIRef(concat_prefix_to_entity_or_property("born_in"))
bday_is = rdflib.URIRef(concat_prefix_to_entity_or_property("bday"))
prime_minister_of = rdflib.URIRef(concat_prefix_to_entity_or_property("prime_minister_of"))
capital_of = rdflib.URIRef(concat_prefix_to_entity_or_property("capital_of"))
area_of = rdflib.URIRef(concat_prefix_to_entity_or_property("area_of"))
government_form_of = rdflib.URIRef(concat_prefix_to_entity_or_property("government_form_of"))
official_language_of = rdflib.URIRef(concat_prefix_to_entity_or_property("official_language_of"))


def alpha_words(word):
    lst = word.split(" ")
    for w in lst:
        if (not w.isalpha()) and ('-' not in w) and ('–' not in w):
            return False
    return True


def replace_space(name):
    name = name.replace(" ", "_")
    name = name.replace("&nbsp", "_")
    return name


def prepare_for_print(answer):
    answer = answer.replace("_", " ")
    return answer


def add_urls(name, url, entity_dict):
    final_url = f"{prefix}{url}"
    if final_url not in visited:
        entity_dict[name] = final_url
        visited.add(final_url)


def initiate_url_dict():
    r = requests.get(first_url)
    doc = lxml.html.fromstring(r.content)
    cnt = 0
    for t in doc.xpath("//table/tbody//td[1]//span/a"):
        name = str(t.attrib['href']).split("/")[-1].replace("_", " ")
        if name[-1] == ')':
            index = name.index('(')
            name = name[:index - 1]
        if name[-1] == ']':
            index = name.index('[')
            name = name[:index - 1]
        name = urllib.parse.unquote(name)
        add_urls(name, t.attrib['href'], countries_url_dict)
        cnt += 1
    add_urls("Channel Islands", "/wiki/Channel_Islands", countries_url_dict)
    add_urls("Western Sahara", "/wiki/Western_Sahara", countries_url_dict)
    add_urls("Afghanistan", "/wiki/Afghanistan", countries_url_dict)
    # print("Countries: " + str(cnt+3))


def ie_countries():
    cnt_c = cnt_a = cnt_p = cnt_g = cnt_pr = cnt_pm = 0
    for country_tuple in countries_url_dict.items():
        url = country_tuple[1]
        Country = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(country_tuple[0])))
        r = requests.get(url)
        doc = lxml.html.fromstring(r.content)
        # getting capitals
        t = doc.xpath("//table[contains(@class, 'infobox')]/tbody//tr[contains(th/text(),'Capital')]//a")
        if len(t) != 0 and t[0].text != "de jure" and "note" not in t[0].text:
            name = t[0].attrib['href'].split("/")
            name = name[-1]
            if name[-1] == ')':
                index = name.index('(')
                name = name[:index - 1]
            if name[-1] == ']':
                index = name.index('[')
                name = name[:index - 1]
            # print(name)
            name = urllib.parse.unquote(name)
            # print("fixed: " + country_tuple[0]+ " :"+name)
            Capital = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(name)))
            g.add((Capital, capital_of, Country))
            cnt_c += 1

        # getting area
        t = doc.xpath(
            "//table[contains(@class,'infobox')]//tr[contains(th//text(),'Area')]/following-sibling::tr/td/text()")
        if len(t) != 0:
            area = t[0].split(" ")
            # print(country_tuple[0])
            # print(area)
            area = ''.join(x for x in area[0] if x.isdigit() or x == "," or x == "." or x == "–")
            print(area)
            if country_tuple[0] == "Channel Islands":
                area = "198"
            Area = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(area)))
            g.add((Area, area_of, Country))
            cnt_a += 1

        # getting government form
        gov = doc.xpath("//table[contains(@class, 'infobox')]/tbody//tr[contains(th//text(), 'Government')]/td//a")
        lst = []
        if len(gov) != 0:
            cnt_g += 1
            for t in gov:
                form = t.text
                link = f"{prefix}{t.attrib['href']}"
                if alpha_words(form):
                    if "/wiki/List_of_countries_by_system_of_government" in link:
                        x = link.split("#")
                        Government = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(x[-1])))
                        g.add((Government, government_form_of, Country))
                        lst.append(x[-1])
                        continue
                    # r = requests.get(link)
                    # doc_2 = lxml.html.fromstring(r.content)
                    title = link.split("/")
                    form = title[-1]
                    if "#" in form:
                        title = form.split("#")
                        form = title[0]
                    if form == 'Marxism%E2%80%93Leninism':
                        form = 'Marxism_Leninism'
                    Government = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(form)))
                    g.add((Government, government_form_of, Country))
                    lst.append(form)
            # print(country_tuple[0]+": "+str(lst))

        # getting population
        t = doc.xpath(
            "//table[contains(@class, 'infobox')]/tbody//tr[contains(th//text(), 'Population')]/following-sibling::tr/td//text()")
        if len(t) != 0:
            pop = t[0]
            if country_tuple[0] == "Russia" or country_tuple[0] == "Dominican Republic":
                pop = t[1]
                pop = ''.join(x for x in pop if x.isdigit() or x == ",")
            elif country_tuple[0] == "Channel Islands":
                pop = "170,499"
            elif country_tuple[0] != "Eritrea":
                lst = pop.split(" ")
                for y in lst:
                    pop = y
                    if "," in y:
                        break
                pop = pop.replace(".", ",")
                pop = ''.join(x for x in pop if x.isdigit() or x == ",")
            Population = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(pop)))
            # print(country_tuple[0] +" :" + pop)
            cnt_p += 1
            g.add((Population, population_of, Country))

        # getting president
        t = doc.xpath('//table[contains(@class, "infobox")]/tbody//tr[th//text()="President"]/td//a')
        if country_tuple[0] == "Switzerland":
            name = "Ignazio Cassis"
            President = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(name)))
            add_urls(name, "/wiki/Ignazio_Cassis", people_url_dict)
            g.add((President, president_of, Country))
            cnt_pr += 1
        if len(t) != 0:
            cnt_pr += 1
            name = t[0].attrib['href'].split("/")[-1]
            if name[-1] == ')':
                index = name.index('(')
                name = name[:index - 1]
            if name[-1] == ']':
                index = name.index('[')
                name = name[:index - 1]
            name = urllib.parse.unquote(name)
            President = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(name)))
            add_urls(name, t[0].attrib['href'], people_url_dict)
            g.add((President, president_of, Country))

        # getting prime minister
        t = doc.xpath('//table[contains(@class, "infobox")]/tbody//tr[th//text()="Prime Minister"]/td//a')
        if country_tuple[0] == "The Bahamas":
            name = "Philip Davis"
            Prime = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(name)))
            add_urls(name, t[0].attrib['href'], people_url_dict)
            g.add((Prime, prime_minister_of, Country))
        elif len(t) != 0:
            cnt_pm += 1
            name = t[0].attrib['href'].split("/")[-1]
            if name[-1] == ')':
                index = name.index('(')
                name = name[:index - 1]
            if name[-1] == ']':
                index = name.index('[')
                name = name[:index - 1]
            name = urllib.parse.unquote(name)
            Prime = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(name)))
            add_urls(name, t[0].attrib['href'], people_url_dict)
            # print(country_tuple[0] + ": " + t[0].text + ", after change:"+name)
            g.add((Prime, prime_minister_of, Country))
        elif country_tuple[0] == "United Arab Emirates":
            t = doc.xpath('//*[@id="mw-content-text"]/div[1]/table[1]/tbody/tr[15]/td/a')
            name = t[0].attrib['href'].split("/")[-1]
            name = urllib.parse.unquote(name)
            Prime = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(name)))
            add_urls(name, t[0].attrib['href'], people_url_dict)
            # print(country_tuple[0] + ": " + t[0].text)
            g.add((Prime, prime_minister_of, Country))
            cnt_pm += 1

    # print("capitals: " + str(cnt_c) + ", area: " + str(cnt_a) + ", population: " + str(cnt_p) + " ,gov form: " + str(
    #   cnt_g) + " ,president: " + str(cnt_pr) + " ,prime minister: " + str(cnt_pm))


def ie_people():
    for person_tuple in people_url_dict.items():
        url = person_tuple[1]
        person = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(person_tuple[0])))
        r = requests.get(url)
        doc = lxml.html.fromstring(r.content)
        # get birth date
        temp = doc.xpath(
            '//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]//span[@class="bday"]//text()')
        bday = " "
        if len(temp) != 0:
            bday = temp[0]
            if temp[0] == ' ' and len(temp) > 1:
                bday = temp[1]
            if bday != ' ' or bday != '':
                date = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(temp[0])))
                g.add((person, bday_is, date))
        place = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]/td//text()')
        arr = []
        for p in place:
            arr.append(p)
        temp = get_right_url(arr)
        if temp == "":
            continue
        country = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(temp)))
        g.add((person, born_in, country))
        # print(person_tuple[0] + ": " + bday + " <-> " + temp)


def get_right_url(arr):
    temp = ''
    for i in range(len(arr)):
        temp = arr[-1]
        if temp[-1] == ')':
            for j in range(len(arr)):
                if ('(') in arr[-1]:
                    arr = arr[:-1]
                    break
                arr = arr[:-1]
            continue
        if temp[-1] == ']':
            for j in range(len(arr)):
                if ('[') in arr[-1]:
                    arr = arr[:-1]
                    break
                arr = arr[:-1]
            continue
        if temp[-1] == ' ':
            arr = arr[:-1]
            continue
        break
    if len(temp) == 0 or has_numbers(temp):
        return ""
    temp = temp.split(",")
    temp = temp[-1].lstrip()
    return temp


def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)


def create():
    initiate_url_dict()
    ie_countries()
    ie_people()
    g.serialize("ontology.nt", format="nt", errors="ignore")


def question():
    g2 = rdflib.Graph()
    g2.parse("ontology.nt", format='nt')
    qs = str(sys.argv[2])
    qs = " ".join(qs.split())
    pram2 = ""
    president = True
    # q1
    if "Who is the president of" in qs:
        pram1 = replace_space(qs[24:-1])
        number = 1
    # q2
    elif "Who is the prime minister of" in qs:
        pram1 = replace_space(qs[29:-1])
        number = 2
    # q3
    elif "What is the population of" in qs:
        pram1 = replace_space(qs[26:-1])
        number = 3
    # q4
    elif "What is the area of" in qs:
        pram1 = replace_space(qs[20:-1])
        number = 4
    # q5
    elif "What is the form of government in" in qs:
        pram1 = replace_space(qs[34:-1])
        number = 5
    # q6
    elif "What is the capital of" in qs:
        pram1 = replace_space(qs[23:-1])
        number = 6
    # q7
    elif "When was the president of" in qs:
        pram1 = replace_space(qs[26:-6])
        number = 7
    # q8
    elif "Where was the president of" in qs:
        pram1 = replace_space(qs[27:-6])
        number = 8
    # q9
    elif "When was the prime minister of" in qs:
        pram1 = replace_space(qs[31:-6])
        number = 9
    # q10
    elif "Where was the prime minister of" in qs:
        pram1 = replace_space(qs[32:-6])
        number = 10
    # q11
    elif "Who is" in qs:
        pram1 = replace_space(qs[7:-1])
        number = 11
        q = query(number, pram1)
        x1 = g2.query(q[0])
        if len(list(x1)) == 0:
            q = q[1]
        else:
            q = q[0]
            president = False
    # q12
    elif "How many" in qs and "are also" in qs:
        i = qs.index("are also")
        pram1 = replace_space(qs[9:i - 1])
        pram2 = replace_space(qs[i + 9:-1])
        number = 12
    # q13
    elif "List all countries whose capital name contains the string" in qs:
        i = qs.index("string")
        pram1 = replace_space(qs[i + 7:])
        number = 13
    # q14
    elif "How many presidents were born in" in qs:
        i = qs.index("in")
        pram1 = replace_space(qs[i + 3:-1])
        number = 14
    # q15
    elif "Is" in qs and "bigger than" in qs:
        i = qs.index("bigger")
        pram1 = replace_space(qs[3:i-1])
        pram2 = replace_space(qs[i + 12:-1])
        q1 = query(4, pram1, "")
        q2 = query(4, pram2, "")
        x = g2.query(q1)
        x = list(x)
        area_1 = prepare_for_print(x[0][0].split("/")[-1])
        x = g2.query(q2)
        x = list(x)
        area_2 = prepare_for_print(x[0][0].split("/")[-1])
        if pram1 == "Israel":
            area_1 = 20770
            area_2 = area_2.replace(",", "")
        elif pram2 == "Israel":
            area_2 = 20770
            area_1 = area_1.replace(",", "")
        else:
            area_1 = area_1.replace(",","")
            area_2 = area_2.replace(",","")
        area_1 = int(area_1)
        area_2 = int(area_2)
        if area_1 > area_2:
            print("Yes, " + pram1 + " is bigger than " + pram2)
        else:
            print("No, " + pram2 + " is bigger than " + pram1)
        return 0
    if number != 11:
        q = query(number, pram1, pram2)
    else:
        x = g2.query(q)
        x = list(x)
        if president:
            print("President of " + prepare_for_print(x[0][0].split("/")[-1]))
        else:
            print("Prime Minister of " + prepare_for_print(x[0][0].split("/")[-1]))
        return
    x = g2.query(q)
    x = list(x)
    if len(x) == 1:
        if prefix_for_ontology in x[0][0]:
            if number != 4:
                print(prepare_for_print(x[0][0].split("/")[-1]))
            else:
                print(prepare_for_print(x[0][0].split("/")[-1]) + " km squared")
        else:
            print(x[0][0])
    else:
        res = []
        for i in range(len(x)):
            res.append(prepare_for_print(x[i][0].split("/")[-1]))
        res.sort()
        st = res[0]
        for i in range(1, len(res)):
            st += ", " + res[i]
        print(st)
    return 0

def query(number, pram1, pram2=""):
    if number == 1:
        q = "select ?pm where { ?pm <http://example.org/president_of> <http://example.org/" + pram1 + ">.} "
    if number == 2:
        q = "select ?pm where { ?pm <http://example.org/prime_minister_of> <http://example.org/" + pram1 + "> . } "
    if number == 3:
        q = "select ?pm where { ?pm <http://example.org/population_of> <http://example.org/" + pram1 + ">.} "
    if number == 4:
        q = "select ?a where { ?a <http://example.org/area_of> <http://example.org/" + pram1 + "> . } "
    if number == 5:
        q = "select ?pm where { ?pm <http://example.org/government_form_of> <http://example.org/" + pram1 + ">.} "
    if number == 6:
        q = "select ?c where { ?c <http://example.org/capital_of> <http://example.org/" + pram1 + "> . } "
    if number == 7:
        q = "select ?b where { ?p <http://example.org/president_of> <http://example.org/" + pram1 + ">. " \
                                                                                                    "?p <http://example.org/bday> ?b . }"
    if number == 8:
        q = "select ?bp where { ?p <http://example.org/president_of> <http://example.org/" + pram1 + "> ." \
                                                                                                     "?p <http://example.org/born_in> ?bp .} "
    if number == 9:
        q = "select ?b where { ?p <http://example.org/prime_minister_of> <http://example.org/" + pram1 + ">. " \
                                                                                                         "?p <http://example.org/bday> ?b . }"
    if number == 10:
        q = "select ?bp where { ?p <http://example.org/prime_minister_of> <http://example.org/" + pram1 + "> ." \
                                                                                                          " ?p <http://example.org/born_in> ?bp .} "
    if number == 11:
        q1 = "select ?c where { <http://example.org/" + pram1 + "> <http://example.org/prime_minister_of> ?c . }"
        q2 = "select ?c where { <http://example.org/" + pram1 + "> <http://example.org/president_of> ?c . }"
        q = [q1, q2]
    if number == 12:
        q = "select (COUNT(*) AS ?count)" \
            "where{<http://example.org/" + pram1 + "> <http://example.org/government_form_of> ?c ." \
                                                   "<http://example.org/" + pram2 + "> <http://example.org/government_form_of> ?c ." \
                                                                                    "}"
    if number == 13:
        q = "select ?country where {?capital <http://example.org/capital_of> ?country . " \
            f'FILTER(CONTAINS(lcase(str(?capital)), "{pram1}")) .' + "}"

    if number == 14:
        q = "select (COUNT(*) AS ?count) " \
            "where {?p <" + prefix_for_ontology + "born_in> <" + prefix_for_ontology + pram1 + ">." \
                                                                                               "?p <" + prefix_for_ontology + "president_of> ?c." \
                                                                                                                              "}"
    return q


def main():
    str = sys.argv[1]
    if str == "create":
        create()
    elif str == "question":
        question()
    else:
        print("unknown command, please check again")
    return 0


main()
