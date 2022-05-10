import lxml.html
import rdflib
import requests

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
    return name.replace(" ", "_").lower()


def add_urls(name, url, entity_dict):
    final_url = f"{prefix}{url}"
    if final_url not in visited:
        entity_dict[name] = final_url
        visited.add(final_url)


def initiate_url_dict():
    r = requests.get(first_url)
    doc = lxml.html.fromstring(r.content)
    cnt = 0
    for t in doc.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table/tbody//td[1]//span/a"):
        add_urls(t.text, t.attrib['href'], countries_url_dict)
        cnt += 1
    add_urls("Channel Islands", "/wiki/Channel_Islands", countries_url_dict)
    add_urls("Western Sahara", "/wiki/Western_Sahara", countries_url_dict)
    add_urls("Afghanistan", "/wiki/Afghanistan", countries_url_dict)


def ie_countries():
    cnt = 0
    for country_tuple in countries_url_dict.items():
        url = country_tuple[1]
        Country = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(country_tuple[0])))
        r = requests.get(url)
        doc = lxml.html.fromstring(r.content)
        # getting capitals
        t = doc.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[contains(@class,'infobox')]//tr[contains(th/text("
                      "),'Capital')]//a/text()")
        if len(t) != 0 and t[0] != "de jure":
            Capital = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(t[0])))
            g.add((Capital, capital_of, Country))

        # getting area
        t = doc.xpath(
            "/html/body/div[3]/div[3]/div[5]/div[1]/table[contains(@class,'infobox')]//tr[contains(th//text(), "
            "'Area')]/following-sibling::tr/td/text()")
        if len(t) != 0:
            area = t[0].split(" ")
            area = area[0] + " km squared"
            Area = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(area)))
            g.add((Area, area_of, Country))

        # getting government form
        gov = doc.xpath(
            "/html/body/div[3]/div[3]/div[5]/div[1]/table[contains(@class,'infobox')]//tr[contains(th//text(), "
            "'Government')]/td//a")
        lst = []
        if len(gov) != 0:
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
                    form=title[-1]
                    if "#" in form:
                        title = form.split("#")
                        form = title[0]
                    Government = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(form)))
                    g.add((Government, government_form_of, Country))
                    lst.append(form)
            #print(country_tuple[0]+": "+str(lst))


        #getting population
        t = doc.xpath(
            "/html/body/div[3]/div[3]/div[5]/div[1]/table[contains(@class,'infobox')]//tr[contains(th//text(), "
            "'Population')]/following-sibling::tr/td//text()")
        if len(t) != 0:
            pop = t[0]
            if country_tuple[0]== "Russia" or country_tuple[0]== "Dominican Republic":
                pop = t[1]
                pop = ''.join(x for x in pop if x.isdigit() or x == ",")
            elif country_tuple[0]=="Channel Islands":
                pop = "170,499"
            elif country_tuple[0]!= "Eritrea":
                lst = pop.split(" ")
                for y in lst:
                    pop = y
                    if "," in y:
                        break
                pop = pop.replace(".",",")
                pop = ''.join(x for x in pop if x.isdigit() or x == ",")
            Population = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(pop)))
            # print(country_tuple[0] +" :" + pop)
            # cnt+=1
            g.add((Population, population_of, Country))


        #getting president
        t = doc.xpath('//table[contains(@class, "infobox")]/tbody//tr[th//text()="President"]/td/a')
        if len(t) != 0:
            #cnt+=1
            President = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(t[0].text)))
            add_urls(t[0].text,t[0].attrib['href'],people_url_dict)
            g.add((President, president_of, Country))


        #getting prime misiter
        t = doc.xpath('//table[contains(@class, "infobox")]/tbody//tr[th//text()="Prime Minister"]/td/a')
        if len(t) != 0:
            cnt+=1
            Prime = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(t[0].text)))
            add_urls(t[0].text,t[0].attrib['href'],people_url_dict)
            #print(country_tuple[0] + ": "+t[0].text)
            g.add((Prime, prime_minister_of, Country))



    #print(cnt)

def ie_people():
    for person_tuple in people_url_dict.items():
        url = person_tuple[1]
        person = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(person_tuple[0])))
        r = requests.get(url)
        doc = lxml.html.fromstring(r.content)
        #get birth date
        temp = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]//span[@class="bday"]//text()')
        bday= " "
        if len(temp) != 0:
            bday = temp[0]
            date = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(temp[0])))
            g.add((person, bday_is, date))
        place = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]/td//text()')
        for p in place:
            k = p
        k = str(k).split(",")
        if len(k)==1:
            temp = k[0].lstrip()
        else:
            temp = k[-1].lstrip()
        country = rdflib.URIRef(concat_prefix_to_entity_or_property(replace_space(temp)))
        g.add((person,born_in,country))
        print(person_tuple[0] + ": " + bday + temp)


initiate_url_dict()
ie_countries()
ie_people()
# g.serialize("ontology.nt", format="nt")
