// The same fortnightly selection for all visitors, using New York dates.
(() => {
    'use strict';

    const couplets = [
        { id: 127, hindi: [
            'कितने अर्थों को संकेतों से बतला जाता साकी,',
            'फिर भी पीनेवालों को है एक पहेली मधुशाला।'
        ], english: [
            'The cupbearer hints at many meanings;',
            'yet to those who drink, the tavern remains a riddle.'
        ] },
        { id: 119, hindi: [
            'इस उधेड़-बुन में ही मेरा सारा जीवन बीत गया—',
            'मैं मधुशाला के अंदर या मेरे अंदर मधुशाला!'
        ], english: [
            'My whole life passed in this perplexity—',
            'am I within the tavern, or is the tavern within me?'
        ] },
        { id: 131, hindi: [
            'मेरे साकी में सबने अपना प्यारा साकी देखा,',
            'जिसकी जैसी रुचि थी उसने वैसी देखी मधुशाला।'
        ], english: [
            'In my cupbearer, each saw the cupbearer they held dear;',
            'each saw the tavern according to their own inclinations.'
        ] },
        { id: 43, hindi: [
            'लोल हिलोरें साकी बन बन माणिक मधु से भर जातीं,',
            'हंस मत्त होते पी पीकर मानसरोवर मधुशाला।'
        ], english: [
            'The dancing waves become cupbearers, brimming with ruby wine;',
            'the swans drink in rapture—Manasarovar becomes a tavern.'
        ] },
        { id: 28, hindi: [
            'बनी रहे वह मदिर पिपासा तृप्त न जो होना जाने,',
            'बने रहें ये पीने वाले, बनी रहे यह मधुशाला।'
        ], english: [
            'May that thirst for wine endure, never knowing satisfaction;',
            'may these drinkers remain, and may this tavern endure.'
        ] },
        { id: 57, hindi: [
            'सभी जाति के लोग यहाँ पर साथ बैठकर पीते हैं,',
            'सौ सुधारकों का करती है काम अकेले मधुशाला।'
        ], english: [
            'People of every caste sit here and drink together;',
            'the tavern alone does the work of a hundred reformers.'
        ] }
    ];

    const DAY = 86400000;
    const START = Date.UTC(2026, 9, 28);

    function shuffle(ids, seed) {
        const result = [...ids];
        let state = seed >>> 0;
        for (let i = result.length - 1; i > 0; i--) {
            state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
            const j = Math.floor((state / 4294967296) * (i + 1));
            [result[i], result[j]] = [result[j], result[i]];
        }
        return result;
    }

    function rawCycle(cycle) {
        if (cycle === 0) return [119, ...shuffle([127, 131, 43, 28, 57], 20261028)];
        return shuffle(couplets.map(quote => quote.id), 20261028 + cycle);
    }

    function cycleOrder(cycle) {
        const order = rawCycle(cycle);
        // Only the first two positions change, so the previous cycle's last is stable.
        if (cycle > 0 && order[0] === rawCycle(cycle - 1).at(-1)) {
            [order[0], order[1]] = [order[1], order[0]];
        }
        return order;
    }

    function easternDate(now = new Date()) {
        const parts = new Intl.DateTimeFormat('en-US', {
            timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit'
        }).formatToParts(now);
        const part = type => parts.find(p => p.type === type).value;
        return `${part('year')}-${part('month')}-${part('day')}`;
    }

    function fillLines(element, lines) {
        element.replaceChildren(...lines.map(line => {
            const span = document.createElement('span');
            span.textContent = line;
            return span;
        }));
    }

    function refreshQuote() {
        const figure = document.querySelector('.madhushala-quote');
        if (!figure) return;
        const day = Date.parse(easternDate() + 'T00:00:00Z');
        const period = Math.floor((day - START) / (14 * DAY));
        const id = period < 0 ? 127 : cycleOrder(Math.floor(period / 6))[period % 6];
        if (figure.dataset.couplet === String(id)) return;
        const quote = couplets.find(item => item.id === id);
        fillLines(figure.querySelector('blockquote'), quote.hindi);
        fillLines(figure.querySelector('.couplet-translation p'), quote.english);
        figure.dataset.couplet = String(id);
    }

    refreshQuote();
    window.addEventListener('focus', refreshQuote);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) refreshQuote();
    });
    // Also refresh tabs left open across a scheduled change.
    window.setInterval(refreshQuote, 60000);
})();
