import React from 'react';
import { Hero } from '@/components/Hero';
import ContactDetails from '../components/ContactDetails';
import OtherSites from '../components/OtherSites';
import allbikesLogo from '@/assets/allbikes_logo.webp';
import foreverFlowerLogo from '@/assets/foreverflower_logo.png';
import { assetSrc } from '@/lib/assets';

const otherSitesData = [
    {
        name: "AllBikes & Scooters",
        logoSrc: assetSrc(allbikesLogo), 
        description: "Your one-stop shop for motorcycle and scooter servicing and parts in Perth, Western Australia.",
        url: "https://www.scootershop.com.au", 
    },
    {
        name: "FutureFlower",
        logoSrc: assetSrc(foreverFlowerLogo), 
        description: "The only annual flower subscription app in existence. Pre arrange flowers to be sent to someone for anniversaries, birthdays, or just because on the same date every year.",
        url: "https://www.futureflower.app", 
    },
];

const ContactPage: React.FC = () => {
    const description = "Have questions, suggestions, or feedback? Get in touch with us. I'd love to hear from you. This is a very new site and I know that there is room for improvement! ethanbetts63@gmail.com";

    return (
        <div>
            <Hero
                title="Contact Us"
                subtitle={description}
                imageAlt="A pin up board of postnotes with various reminder icons"
            />
            
            <div style={{ backgroundColor: 'var(--color1)' }}>
                <ContactDetails />
                <OtherSites sites={otherSitesData} />
            </div>
        </div>
    );
};


export default ContactPage;
