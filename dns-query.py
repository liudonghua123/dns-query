#!/usr/bin/env python3
# coding=utf-8

import argparse
import os
import logging
import sys
import dns.resolver

resolver = dns.resolver.Resolver()
resolver.nameservers = ['113.55.13.51']

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def normalizeOuputPath(inputPath):
    fileName = os.path.basename(inputPath)
    lastDotPosition = fileName.rfind(".")
    return os.path.join(os.path.dirname(inputPath), fileName[:lastDotPosition] + "-result" + '.xlsx')

def parseArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="The input dns query file")
    parser.add_argument("-o", "--output", help="The output result file")
    args = parser.parse_args()
    if not args.input:
        args.input = 'DNS解析.txt'
        logger.info("Not specify input, use the default {input}".format(input=args.input))
    if not os.path.exists(args.input):
        logger.error("The input file of {input} not exits".format(input=args.input))
        sys.exit()
    if not args.output:
        args.output = normalizeOuputPath(args.input)
    logger.info("The input file is {input}".format(input=args.input))
    logger.info("The output file is {output}".format(output=args.output))
    return args.input, args.output

def query(domain, queryTypes):
    queryResult = {'domain': domain}
    for queryType in queryTypes:
        queryResult[queryType] = []
        try:
            logger.debug("querying {domain} {queryType} record".format(queryType=queryType, domain=domain))
            answer = resolver.query(domain, queryType)
            for rdata in answer:
                queryResult[queryType].append(rdata.to_text())
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers) as e:
            queryResult[queryType] = []
            logger.debug("{domain} has no {queryType} record".format(queryType=queryType, domain=domain))
    return queryResult

def processDNSQuery(inputFile, queryTypes):
    result = []
    with open(inputFile, 'r') as fp:
        read_lines = fp.readlines()
        read_lines = [line.rstrip('\n') for line in read_lines]
        for domain in read_lines:
            queryResult = query(domain, queryTypes)
            result.append(queryResult)
            logger.info("query {domain} with queryResult: {queryResult}".format(domain=domain, queryResult=queryResult))
    return result

def writeResultToExcel(queryResults, output):
    logger.debug("Starting write result to excel file {output}".format(output=output))
    import pandas as pd
    df = pd.DataFrame(queryResults, columns=['domain', 'A', 'AAAA', 'CNAME'])
    with pd.ExcelWriter(output) as writer:
        df.to_excel(writer,'Sheet1')

if __name__ == "__main__":
    input, output = parseArgument()
    queryTypes = ['A', 'AAAA', 'CNAME']
    queryResults = processDNSQuery(input, queryTypes)
    writeResultToExcel(queryResults, output)

